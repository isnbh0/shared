"""pi (earendil) CLI backend for SkillOpt.

Two roles, one module:
  * pi_chat  -- single-shot `pi -p --mode json --no-tools` chat (optimizer / chat-target).
  * pi_exec  -- agentic `pi -p --mode json` rollout target (tools ON, one skill loaded),
                dispatched from codex_harness.run_target_exec like codex_exec/claude_code_exec.
                (Added in Phase 2.)

Structure mirrors codex_backend.py. The prompt-flattening / attachment / compat-message
helpers are reused verbatim from codex_backend; only the pi-specific subprocess argv,
JSONL stream parsing, usage-field mapping, and billing guards are new.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
from typing import Any

from skillopt.model.common import (
    tracker,
)
# Reuse the codex prompt/compat plumbing verbatim (identical OpenAI-message contract).
from skillopt.model.codex_backend import (
    _build_prompt_from_messages,
    _compat_message_from_payload,
    _materialize_attachments,
)


# --- module config (env-overridable, mutated by the setters below) ----------
PI_BIN = os.environ.get("PI_CLI_BIN", "pi")
# Fallback provider, used ONLY when a per-role deployment string carries a bare model with no
# `provider/` prefix. A per-role deployment like `zai/glm-5.2` or `openai-codex/gpt-5.5`
# overrides this (see Multi-model routing). openai-codex == ChatGPT Plus/Pro OAuth (a true
# non-metered subscription) is a safe default, but any pinned provider is honored -- pi is
# genuinely multi-model on this machine (GLM/zai, openai-codex, anthropic-OAuth, ...).
PI_PROVIDER = os.environ.get("PI_PROVIDER", "openai-codex")

OPTIMIZER_DEPLOYMENT = os.environ.get("OPTIMIZER_DEPLOYMENT", "gpt-5.5")
TARGET_DEPLOYMENT = os.environ.get("TARGET_DEPLOYMENT", "gpt-5.5")

# "Block accidental, allow intentional." Under the skillopt-oauth wrapper two provider sets
# decide what may run; plain skillopt-train applies no pre-spawn gate. SUBSCRIPTION_PROVIDERS is
# the built-in never-metered set (true subscription OAuth). The allowed-metered set is a
# user-opt-in list of metered providers the operator DELIBERATELY enables (e.g. zai/GLM, or
# anthropic/Claude-OAuth) via config pi_allowed_metered_providers (PI_ALLOW_METERED overrides),
# resolved live in _permitted_providers.
# A spawn is permitted iff the resolved provider is in the union. anthropic is in NEITHER set by
# default: even under a Pro/Max OAuth token, third-party-harness use bills per-token "extra
# usage", so it is only reachable via an explicit allowed-metered opt-in.
SUBSCRIPTION_PROVIDERS = frozenset(
    p.strip()
    for p in os.environ.get("PI_SUBSCRIPTION_PROVIDERS", "openai-codex,github-copilot").split(",")
    if p.strip()
)


def _permitted_providers() -> frozenset[str]:
    """Providers a spawn may use under the wrapper: subscription set ∪ the allowed-metered set.
    The allowed-metered set has a SINGLE source of truth -- the config key
    pi_allowed_metered_providers -- with PI_ALLOW_METERED as an explicit override. The oauth
    wrapper resolves that set once (config, env override) before spawn and exports it into
    PI_ALLOW_METERED, so this child-side gate and the wrapper's preflight (_probe_pi_oauth) always
    see the IDENTICAL set. Read live so the wrapper's export or a test is honored without
    re-import."""
    allowed = frozenset(
        p.strip() for p in os.environ.get("PI_ALLOW_METERED", "").split(",") if p.strip()
    )
    return SUBSCRIPTION_PROVIDERS | allowed


def _enforce_provider_gate() -> bool:
    """True only under the skillopt-oauth wrapper, which exports the DEDICATED flag
    SKILLOPT_OAUTH_ENFORCE=1 into the child env (oauth_guard.main). This is a purpose-built
    wrapper-mode signal, distinct from SKILLOPT_OAUTH_RUN_ID (which continues to identify the run,
    not to gate providers). Plain skillopt-train leaves it unset, so the pre-spawn gate is a no-op
    and any pinned provider runs at the user's discretion. The actual==intended runtime guard
    (_guard_provider) runs regardless, in BOTH modes."""
    return os.environ.get("SKILLOPT_OAUTH_ENFORCE") == "1"

# pi thinking level: off|minimal|low|medium|high|xhigh. None -> "off" for repro.
REASONING_EFFORT: str | None = None
# NOTE: `pi --thinking xhigh` IS accepted by the CLI (exits 0; verified on v0.79.10). The clamp
# in _thinking_level below is therefore DEFENSIVE ONLY -- a gpt-5.x model may not honor xhigh even
# though the CLI parses it. It is not a hard requirement and can be relaxed to include "xhigh" if a
# provider/model is confirmed to accept it.
_VALID_THINKING = {"off", "minimal", "low", "medium", "high"}

# A terse system prompt REPLACES pi's default coding system prompt so a pure chat/optimizer
# call is not polluted by agent tooling guidance. The real instructions ride inside the
# flattened user prompt (exactly as codex does).
_PI_CHAT_SYSTEM = (
    "You are a precise assistant. Read the user message and follow its "
    "instructions exactly. Do not use tools. Return only the requested output."
)


class PiBillingError(RuntimeError):
    """Non-retryable: a metered/fallback provider was requested or served a response."""


def _resolve_provider_model(model: str) -> tuple[str, str]:
    """`provider/model` -> (provider, model); bare `model` -> (PI_PROVIDER, model)."""
    m = str(model or "").strip()
    if "/" in m:
        provider, _, rest = m.partition("/")
        return provider.strip() or PI_PROVIDER, rest.strip()
    return PI_PROVIDER, m


def _assert_allowed_provider(provider: str) -> None:
    """Under the oauth wrapper, fail closed BEFORE spawning pi unless the resolved provider is
    permitted == the built-in subscription set (openai-codex, github-copilot) ∪ the user-opt-in
    allowed-metered set (e.g. zai/GLM or anthropic/Claude-OAuth via config
    pi_allowed_metered_providers, PI_ALLOW_METERED override).

    This is the per-spawn "block accidental, allow intentional" gate: a `provider/model`
    deployment string cannot route an UNINTENDED metered call (an un-opted anthropic/openai/zai
    fallback is refused before pi is launched), while a DELIBERATELY opted-in provider passes.
    Plain skillopt-train does not enforce this (see _enforce_provider_gate); the runtime
    actual==intended guard still applies in both modes.
    """
    if not _enforce_provider_gate():
        return  # plain skillopt-train: no pre-spawn gate; pinned provider is the user's choice
    permitted = _permitted_providers()
    if provider not in permitted:
        raise PiBillingError(
            f"refusing to run pi against provider {provider!r}: not in the permitted set "
            f"{sorted(permitted)!r}. Pin a --provider/--model backed by a subscription OAuth "
            "entry (openai-codex / github-copilot), or opt the provider into the allowed-metered "
            "set (config pi_allowed_metered_providers; PI_ALLOW_METERED overrides)."
        )


def _thinking_level() -> str:
    eff = (REASONING_EFFORT or "").strip().lower()
    if eff in _VALID_THINKING:
        return eff
    if eff in {"xhigh", "max"}:
        return "high"  # DEFENSIVE clamp (see _VALID_THINKING note); the CLI itself accepts xhigh
    return "off"


def _usage_from_message(usage: dict[str, Any] | None) -> dict[str, int]:
    """Map a pi assistant usage object to {prompt,completion,total}.

    pi fields: input, output, cacheRead, cacheWrite, totalTokens. We take pi's own
    `totalTokens` as the source of truth for total (avoids diverging from pi when cacheWrite
    is or is not folded into it), and derive prompt = total - output so prompt+completion
    always equals pi's totalTokens.
    """
    usage = usage or {}
    out = int(usage.get("output", 0) or 0)
    total = usage.get("totalTokens")
    if total is None:
        inp = int(usage.get("input", 0) or 0)
        cache_read = int(usage.get("cacheRead", 0) or 0)
        cache_write = int(usage.get("cacheWrite", 0) or 0)
        total = inp + cache_read + cache_write + out
    total = int(total or 0)
    prompt = max(total - out, 0)
    return {"prompt_tokens": prompt, "completion_tokens": out, "total_tokens": total}


def _add_usage(a: dict[str, int], b: dict[str, int]) -> dict[str, int]:
    return {k: a.get(k, 0) + b.get(k, 0) for k in ("prompt_tokens", "completion_tokens", "total_tokens")}


def _assistant_text(message: dict[str, Any]) -> str:
    parts: list[str] = []
    for block in message.get("content", []) or []:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(str(block.get("text", "") or ""))
    return "".join(parts)


def _parse_pi_stream(stdout: str) -> dict[str, Any]:
    """Parse `pi -p --mode json` JSONL. STRICT LF framing; skip undecodable lines.

    Splitting on "\\n" only (NOT str.splitlines(), which also breaks on U+2028/U+2029/U+0085
    -- code points that are legal inside JSON strings and appear in model output, and would
    cut a message_end object in two so both halves fail json.loads and the answer is lost).

    Returns: last_text, usage (summed over assistant messages), providers_seen (set),
    models_seen (set), usage_without_provider (bool -- fail-closed signal), error (str),
    saw_agent_end (bool). providers_seen/models_seen feed the actual==intended guard.
    """
    last_text = ""
    usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    providers_seen: set[str] = set()
    models_seen: set[str] = set()
    usage_without_provider = False
    error = ""
    saw_agent_end = False

    for raw_line in stdout.split("\n"):
        line = raw_line.strip().strip("\r")
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        ptype = payload.get("type")
        if ptype == "message_end":
            message = payload.get("message", {}) or {}
            if message.get("role") != "assistant":
                continue
            text = _assistant_text(message)
            if text.strip():
                last_text = text
            msg_usage = _usage_from_message(message.get("usage"))
            usage = _add_usage(usage, msg_usage)
            prov = message.get("provider")
            mdl = message.get("model")
            if mdl:
                models_seen.add(str(mdl))
            if prov:
                providers_seen.add(str(prov))
            elif msg_usage["total_tokens"] > 0:
                # Usage was billed but no provider was named -> cannot verify actual==intended.
                usage_without_provider = True
            if message.get("stopReason") == "error":
                error = error or "pi assistant message ended with stopReason=error"
        elif ptype == "agent_end":
            saw_agent_end = True  # agent_end carries no finalError; do not read one
        elif ptype in {"error", "auto_retry_end"}:
            msg = payload.get("message") or payload.get("finalError")
            if msg and not error:
                error = str(msg)

    return {
        "last_text": last_text.strip(),
        "usage": usage,
        "providers_seen": providers_seen,
        "models_seen": models_seen,
        "usage_without_provider": usage_without_provider,
        "error": error,
        "saw_agent_end": saw_agent_end,
    }


def _guard_provider(parsed: dict[str, Any], pinned_provider: str, pinned_model: str) -> None:
    """Fail CLOSED unless pi actually served the response from the PINNED provider AND model.

    Verifies actual == intended on every spawn, in BOTH operating modes. This is what catches a
    SILENT fallback to pi's ambient default -- GLM/zai, anthropic, openai, or anything else. It
    does NOT consult the permitted-provider set, so a deliberately pinned provider (incl. an
    opted-in metered one like zai/glm-5.2) passes as long as pi actually served it. Raises
    PiBillingError (non-retryable). pi echoes provider/model VERBATIM as the CLI args in the
    message_end event (confirmed: "openai-codex"/"gpt-5.5"), so this string comparison is valid.
    Failure modes, all fatal:
      * the pinned provider absent from what actually served the response (provider fallback);
      * the pinned model absent from what actually served the response (model fallback);
      * usage billed but no provider named (cannot prove actual==intended -> refuse to trust).
    """
    seen = parsed["providers_seen"]
    seen_models = parsed["models_seen"]
    if parsed["usage_without_provider"] and not seen:
        raise PiBillingError(
            "pi billed usage but named no provider; cannot verify actual==intended -- refusing."
        )
    if seen and pinned_provider not in seen:
        raise PiBillingError(
            f"pi provider fallback detected: pinned {pinned_provider!r} but response came from "
            f"{sorted(seen)!r}. Pin a --provider/--model pair that appears in `pi --list-models`."
        )
    if seen_models and pinned_model and pinned_model not in seen_models:
        raise PiBillingError(
            f"pi model fallback detected: pinned model {pinned_model!r} but response came from "
            f"{sorted(seen_models)!r}."
        )


def _has_image_attachment(attachments: list[dict[str, Any]]) -> bool:
    for att in attachments or []:
        kind = str(att.get("type") or att.get("mime_type") or att.get("kind") or "").lower()
        if "image" in kind:
            return True
        name = str(att.get("path") or att.get("filename") or att.get("name") or "").lower()
        if name.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff")):
            return True
    return False


def _run_pi(
    *,
    model: str,
    prompt: str,
    attachments: list[dict[str, Any]],
    structured_output: bool,
    timeout: int | None,
) -> tuple[str, dict[str, int]]:
    """Single-shot pi chat completion. Mirrors codex_backend._run_codex_exec."""
    provider, model_id = _resolve_provider_model(model)
    _assert_allowed_provider(provider)  # refuse BEFORE spawning (wrapper-gated)

    # pi_chat is TEXT-FIRST: it has no vision flag and `@path` positionals inject file
    # CONTENTS as text (garbage for binary images). Refuse image attachments in chat; route
    # vision through pi_exec (files read via tools) instead.
    if _has_image_attachment(attachments):
        raise RuntimeError(
            "pi_chat is text-first: image attachments are not supported (no vision flag; "
            "@path injects raw bytes as text). Route vision tasks through pi_exec."
        )

    with tempfile.TemporaryDirectory(prefix="skillopt_pi_") as temp_dir:
        file_paths = _materialize_attachments(attachments, temp_dir)

        command = [
            PI_BIN, "-p", "--mode", "json",
            "--no-session", "--no-tools",
            "--no-context-files", "--no-extensions", "--no-skills",
            "--no-prompt-templates", "--no-themes", "--no-approve",
            "--provider", provider,
            "--model", model_id,
            "--thinking", _thinking_level(),
            # NEVER pass --api-key: rank-1 resolution would override the auth.json OAuth entry.
            "--system-prompt", _PI_CHAT_SYSTEM,
        ]
        # No chat --schema flag; structured JSON is prompt-guided (the flattened prompt
        # already appends the assistant-message schema instruction). We parse/validate here.
        _ = structured_output

        command.append(prompt)  # single positional == the user turn
        for file_path in file_paths:  # text attachments only (images refused above)
            command.append(f"@{file_path}")

        proc = subprocess.run(
            command, text=True, capture_output=True, timeout=timeout, check=False,
            stdin=subprocess.DEVNULL,  # one-shot: prompt is an argv positional, never stdin
        )

        # SUCCESS IS DERIVED FROM THE STREAM, NEVER FROM proc.returncode. pi exits 0 even on a
        # missing API key / runtime failure and only exits non-zero on a CLI-parse error
        # (unknown provider/flag), so the return code cannot gate success. The authoritative
        # signals are: (a) provider/model matched the pin (_guard_provider, below), (b) no
        # error/fallback event in the stream, and (c) a non-empty assembled final message.
        # returncode is folded into the diagnostic ONLY after the stream is already a failure.
        parsed = _parse_pi_stream(proc.stdout)
        _guard_provider(parsed, provider, model_id)  # actual==intended; non-retryable on fallback

        if parsed["error"] and not parsed["last_text"]:
            raise RuntimeError(f"pi run error: {parsed['error']}")
        if not parsed["last_text"]:
            detail = (parsed["error"] or proc.stderr.strip() or proc.stdout.strip()
                      or f"exit {proc.returncode}")
            raise RuntimeError(f"pi returned an empty final message ({detail})")
        return parsed["last_text"], parsed["usage"]


def _chat_messages_impl(
    model: str,
    messages: list[dict[str, Any]],
    max_completion_tokens: int,
    retries: int,
    stage: str,
    *,
    tools: list[dict[str, Any]] | None = None,
    tool_choice: str | dict[str, Any] | None = None,
    return_message: bool = False,
    timeout: int | None = None,
) -> tuple[Any, dict[str, int]]:
    del max_completion_tokens  # pi has no such CLI flag
    last_err: Exception | None = None
    structured_output = bool(tools) or return_message

    for attempt in range(retries):
        try:
            prompt, attachments = _build_prompt_from_messages(
                messages, tools=tools, tool_choice=tool_choice,
                structured_output=structured_output,
            )
            raw_text, usage_info = _run_pi(
                model=model, prompt=prompt, attachments=attachments,
                structured_output=structured_output, timeout=timeout,
            )
            tracker.record(stage, usage_info["prompt_tokens"], usage_info["completion_tokens"])

            if not structured_output:
                return raw_text, usage_info
            payload = json.loads(raw_text)  # may raise -> retried
            compat = _compat_message_from_payload(payload, tool_choice=tool_choice)
            return (compat if return_message else compat.content), usage_info
        except PiBillingError:
            raise  # billing/fallback failures are FATAL -- never spend more on retries
        except subprocess.TimeoutExpired as exc:
            last_err = RuntimeError(f"pi CLI timed out after {timeout}s") if timeout else exc
        except Exception as exc:  # noqa: BLE001
            last_err = exc
        time.sleep(min(2 ** attempt, 30))

    raise RuntimeError(f"pi call failed after {retries} retries: {last_err}")


# --- public chat surface (identical signatures to codex_backend) ------------
def chat_with_model(model, system, user, max_completion_tokens=16384, retries=5,
                    stage="custom", timeout=None):
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    return _chat_messages_impl(model, messages, max_completion_tokens, retries, stage, timeout=timeout)


def chat_messages_with_model(model, messages, max_completion_tokens=16384, retries=5,
                             stage="custom", *, tools=None, tool_choice=None,
                             return_message=False, timeout=None):
    return _chat_messages_impl(model, messages, max_completion_tokens, retries, stage,
                               tools=tools, tool_choice=tool_choice,
                               return_message=return_message, timeout=timeout)


def chat_optimizer(system, user, max_completion_tokens=16384, retries=5,
                   stage="optimizer", timeout=None):
    return chat_with_model(OPTIMIZER_DEPLOYMENT, system, user, max_completion_tokens,
                           retries, stage, timeout)


def chat_target(system, user, max_completion_tokens=16384, retries=5,
                stage="target", timeout=None):
    return chat_with_model(TARGET_DEPLOYMENT, system, user, max_completion_tokens,
                           retries, stage, timeout)


def chat_with_deployment(deployment, system, user, max_completion_tokens=16384, retries=5,
                         stage="custom", timeout=None):
    return chat_with_model(deployment, system, user, max_completion_tokens, retries, stage, timeout)


def chat_optimizer_messages(messages, max_completion_tokens=16384, retries=5,
                            stage="optimizer", *, tools=None, tool_choice=None,
                            return_message=False, timeout=None):
    return _chat_messages_impl(OPTIMIZER_DEPLOYMENT, messages, max_completion_tokens, retries,
                               stage, tools=tools, tool_choice=tool_choice,
                               return_message=return_message, timeout=timeout)


def chat_target_messages(messages, max_completion_tokens=16384, retries=5,
                         stage="target", *, tools=None, tool_choice=None,
                         return_message=False, timeout=None):
    return _chat_messages_impl(TARGET_DEPLOYMENT, messages, max_completion_tokens, retries,
                               stage, tools=tools, tool_choice=tool_choice,
                               return_message=return_message, timeout=timeout)


def chat_messages_with_deployment(deployment, messages, max_completion_tokens=16384, retries=5,
                                  stage="custom", *, tools=None, tool_choice=None,
                                  return_message=False, timeout=None):
    return _chat_messages_impl(deployment, messages, max_completion_tokens, retries, stage,
                               tools=tools, tool_choice=tool_choice,
                               return_message=return_message, timeout=timeout)


# --- token tracker (shares the common singleton, exactly like codex_backend) -
def get_token_summary():
    return tracker.summary()


def reset_token_tracker():
    tracker.reset()


# --- setters -----------------------------------------------------------------
def set_target_deployment(deployment):
    global TARGET_DEPLOYMENT
    TARGET_DEPLOYMENT = deployment
    os.environ["TARGET_DEPLOYMENT"] = deployment


def set_optimizer_deployment(deployment):
    global OPTIMIZER_DEPLOYMENT
    OPTIMIZER_DEPLOYMENT = deployment
    os.environ["OPTIMIZER_DEPLOYMENT"] = deployment


def set_reasoning_effort(effort):
    global REASONING_EFFORT
    REASONING_EFFORT = effort if effort else None


# ============================================================================
# EXEC role (pi_exec) -- agentic rollout target. Reuses codex_harness plumbing.
# Keep every codex_harness import LAZY (inside functions) -- hoisting to module
# scope deadlocks `import skillopt.model` (codex_harness imports back into model).
# ============================================================================
_PI_TOOL_MAP = {
    "read": "read", "bash": "bash", "write": "write", "edit": "edit",
    "grep": "grep", "find": "find", "ls": "ls", "glob": "find",
}


def _pi_tools(allowed_tools: Any, allow_file_edits: bool) -> str:
    from skillopt.model.codex_harness import _normalize_tools
    raw = "Read,Bash" if allowed_tools is None else _normalize_tools(allowed_tools)
    names: list[str] = []
    for t in str(raw).split(","):
        pi_name = _PI_TOOL_MAP.get(t.strip().lower())
        if pi_name and pi_name not in names:
            names.append(pi_name)
    if allow_file_edits:
        for extra in ("write", "edit"):
            if extra not in names:
                names.append(extra)
    return ",".join(names) or "read,bash"


def _stage_into_workdir(work_dir: str, paths: list[str] | None) -> None:
    """pi has NO dir-mount flag; make external files reachable by copying them under work_dir.

    Copies each path into <work_dir>/_staged/<basename> if it is not already inside work_dir.
    (Directories are copied recursively.) This replaces the invalid --allow-dir approach: pi has
    no --allow-dir/--add-dir flag of any kind, and emitting one produces an unknown-option argv
    error that fails the whole rollout.
    """
    if not paths:
        return
    staged_root = os.path.join(work_dir, "_staged")
    work_real = os.path.realpath(work_dir)
    for src in paths:
        if not src or not os.path.exists(src):
            continue
        if os.path.realpath(src).startswith(work_real + os.sep):
            continue  # already reachable
        os.makedirs(staged_root, exist_ok=True)
        dst = os.path.join(staged_root, os.path.basename(src.rstrip(os.sep)))
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)


def _normalize_pi_exec_prompt(prompt: str) -> str:
    """pi-specific prompt normalizer.

    The harness's generic _exec_prompt steers CLI agents to 'Read the skill file directly;
    do not call a Skill tool.' That wording is correct for codex/claude but CONTRADICTS pi's
    native /skill: mechanism. Strip the anti-Skill-tool guidance so the /skill:skillopt-target
    prefix (which expands SKILL.md inline as pi's sanctioned force-execute form) is not
    self-contradictory.
    """
    banned = (
        "Do not call a Skill tool; the ReflACT guidance is a local markdown file.",
        "do not call a Skill tool",
        "Read .agents/skills/skillopt-target/SKILL.md directly; do not call a Skill tool.",
    )
    out = prompt
    for phrase in banned:
        out = out.replace(phrase, "")
    return " ".join(out.split())


def _run_pi_cli_exec(
    *, work_dir, prompt, model, timeout,
    images=None, data_dirs=None, allowed_tools=None, allow_file_edits=False,
) -> tuple[str, str]:
    """One agentic pi rollout. Mirrors codex_harness._run_claude_code_cli_exec.

    Skill recipe (confirmed on pi v0.79.10): `pi --no-skills --skill <skill_dir> -p --mode json
    "/skill:skillopt-target <task>"` -- the explicit --skill is required for the /skill: prefix to
    force-inject exactly that one skill.
    """
    from skillopt.model.backend_config import get_pi_exec_config
    from skillopt.model.codex_harness import _exec_prompt, _validate_exec_path

    config = get_pi_exec_config()
    provider = str(config.get("provider") or PI_PROVIDER)
    prov_from_model, model_id = _resolve_provider_model(model or "")
    if "/" in str(model or ""):
        provider = prov_from_model  # a provider/model deployment string wins over pi_exec_provider
    _assert_allowed_provider(provider)  # refuse BEFORE spawning (wrapper-gated)

    tools = _pi_tools(allowed_tools, allow_file_edits)

    # pi has no dir-mount flag: stage external data/images INTO the sandbox instead.
    _stage_into_workdir(work_dir, data_dirs)
    _stage_into_workdir(work_dir, images)

    skill_dir = os.path.join(work_dir, ".agents", "skills", "skillopt-target")
    # Force EXACTLY this skill and force it to execute via the /skill: prefix. Use the
    # pi-specific normalizer so the prompt does not carry the contradictory
    # "do not call a Skill tool" wording.
    exec_prompt = "/skill:skillopt-target " + _normalize_pi_exec_prompt(
        _exec_prompt(prompt, allow_file_edits=allow_file_edits)
    )

    command = [
        str(config.get("path") or PI_BIN), "-p", "--mode", "json",
        "--no-session", "--approve",
        "--no-context-files", "--no-extensions",
        "--no-skills", "--skill", _validate_exec_path(skill_dir),
        "--provider", provider, "--model", model_id,
        "--thinking", str(config.get("thinking") or "off"),
        "--tools", tools,
        exec_prompt,
    ]

    try:
        proc = subprocess.run(command, cwd=work_dir, capture_output=True, text=True, timeout=timeout,
                              stdin=subprocess.DEVNULL)  # pi blocks on a startup stdin read under --skill; give it immediate EOF
    except subprocess.TimeoutExpired as exc:
        stdout, stderr = exc.stdout or "", exc.stderr or ""
        raw = stdout if not stderr else (f"{stdout}\n[stderr]\n{stderr}" if stdout else stderr)
        return "", raw

    stdout, stderr = proc.stdout or "", proc.stderr or ""
    raw = stdout if not stderr else (f"{stdout}\n[stderr]\n{stderr}" if stdout else stderr)

    parsed = _parse_pi_stream(stdout)
    _guard_provider(parsed, provider, model_id)  # actual==intended; non-retryable on fallback
    # Real usage (unlike codex_exec's 0/0 stub): SUM across assistant messages (per-turn; json
    # mode has no cumulative-total event).
    tracker.record("rollout", parsed["usage"]["prompt_tokens"], parsed["usage"]["completion_tokens"])

    # Success from the STREAM, never proc.returncode (pi exits 0 even on a runtime failure and
    # non-zero only on a CLI-parse error). An empty assembled final message is the failure
    # signal; run_pi_exec's retry loop handles it.
    response = parsed["last_text"]
    if not response.strip():
        return "", raw
    return response, raw


def run_pi_exec(
    *, work_dir, prompt, model, timeout,
    images=None, data_dirs=None, allowed_tools=None,
    permission_mode=None, allow_file_edits=False,
) -> tuple[str, str]:
    """Exec entry point. Retry/backoff shape mirrors run_claude_code_exec (CLI-only)."""
    from skillopt.model.backend_config import get_pi_exec_config
    from skillopt.model.codex_harness import _retry_prompt, _persist_claude_artifacts

    del permission_mode  # pi trust is handled by --approve; no per-tool prompt mode
    config = get_pi_exec_config()
    retries = int(config.get("empty_response_retries", 0) or 0)
    last_response = ""
    all_raw: list[str] = []

    for attempt in range(retries + 1):
        attempt_prompt = _retry_prompt(prompt, attempt)
        response, raw = _run_pi_cli_exec(
            work_dir=work_dir, prompt=attempt_prompt, model=model, timeout=timeout,
            images=images, data_dirs=data_dirs, allowed_tools=allowed_tools,
            allow_file_edits=allow_file_edits,
        )
        all_raw.append(f"===== PI CLI ATTEMPT {attempt + 1} =====\n{raw}")
        last_response = response
        if response.strip():
            combined = "\n\n".join(all_raw)
            _persist_claude_artifacts(work_dir, combined, response)
            return response, combined

    combined = "\n\n".join(all_raw)
    _persist_claude_artifacts(work_dir, combined, last_response)
    return last_response, combined
