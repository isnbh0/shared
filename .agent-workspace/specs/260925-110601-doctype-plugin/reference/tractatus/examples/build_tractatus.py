# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Build examples/tractatus.{md,html} from the Project Gutenberg TeX of the Ogden Tractatus.

Usage (from the dotfiles root):
    uv run macbook/claude/skills/my-tractatus/examples/build_tractatus.py [--source PATH] [--out-dir DIR]
    uv run macbook/claude/skills/my-tractatus/examples/build_tractatus.py --print-sha256 [--source PATH]
Without --source, downloads SOURCE_URL into a temporary directory.

Law C: TeX becomes a mode-tagged tree through a closed command table (anything else raises
ConversionError), and one mode-aware serializer emits the markdown. `$` is emitted only when
moving from text mode into math mode, so math delimiters never nest, and markdown markers are
never emitted in math mode.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import re
import sys
import tempfile
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import NamedTuple

SOURCE_URL = "https://www.gutenberg.org/files/5740/5740-t/5740-t.tex"
SOURCE_SHA256 = "52158eed80f03552c257e22dca26e1684588814554481242be94063ce9c6061f"
EXPECTED_PROPOSITIONS = 526
HERE = Path(__file__).resolve().parent

_embed_spec = importlib.util.spec_from_file_location("embed", HERE.parent / "embed.py")
embed = importlib.util.module_from_spec(_embed_spec)
_embed_spec.loader.exec_module(embed)

TITLE = "# Tractatus Logico-Philosophicus"
INTRO = "Ludwig Wittgenstein. Translated by C. K. Ogden, 1922. Public domain."


class ConversionError(Exception):
    def __init__(self, number: str | None, message: str):
        super().__init__(message if number is None else f"proposition {number}: {message}")
        self.number = number
        self.message = message


# ── source ────────────────────────────────────────────────────────────────────

ENCODINGS = {"latin1": "latin-1", "latin9": "iso8859-15", "utf8": "utf-8"}


def load_source(data: bytes) -> str:
    digest = hashlib.sha256(data).hexdigest()
    if digest != SOURCE_SHA256:
        raise ConversionError(None, f"source SHA-256 {digest} != pinned {SOURCE_SHA256}")
    # Only a live declaration counts: the pinned source has `%\usepackage[latin1]{inputenc}`
    # commented out and is UTF-8.
    decl = re.search(r"\\usepackage\[([^\]]*)\]\{inputenc\}", strip_comments(data.decode("latin-1")))
    name = decl.group(1) if decl else "utf8"
    if name not in ENCODINGS:
        raise ConversionError(None, f"unsupported inputenc encoding {name!r}")
    return data.decode(ENCODINGS[name])


# ── front end ─────────────────────────────────────────────────────────────────


def strip_comments(tex: str) -> str:
    """Remove each `%` comment (a `%` after an even number of `\\`) with its newline and the
    next line's leading spaces and tabs, as TeX does."""
    out = []
    i = 0
    while i < len(tex):
        c = tex[i]
        if c == "\\":
            out.append(tex[i : i + 2])
            i += 2
        elif c == "%":
            j = tex.find("\n", i)
            i = len(tex) if j == -1 else re.compile(r"[ \t]*").match(tex, j + 1).end()
        else:
            out.append(c)
            i += 1
    return "".join(out)


def read_braced(s: str, i: int) -> tuple[str, int]:
    if i >= len(s) or s[i] != "{":
        raise ConversionError(None, f"expected '{{' at offset {i}")
    depth = 0
    j = i
    while j < len(s):
        c = s[j]
        if c == "\\":
            j += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return s[i + 1 : j], j + 1
        j += 1
    raise ConversionError(None, f"unbalanced group starting at offset {i}")


def _skip_space(s: str, i: int) -> int:
    while i < len(s) and s[i] in " \t\n":
        i += 1
    return i


def extract_propositions(tex: str) -> list[tuple[str, str]]:
    tex = strip_comments(tex.replace("\r\n", "\n").replace("\r", "\n"))
    start = tex.find("\\begin{document}")
    if start == -1:
        raise ConversionError(None, "no \\begin{document}")
    body = tex[start:]
    end = re.search(r"\\PropositionG(?![A-Za-z])", body)
    if end is not None:
        body = body[: end.start()]
    props = []
    for m in re.finditer(r"\\PropositionE(?![A-Za-z])", body):
        number, i = read_braced(body, _skip_space(body, m.end()))
        text, _ = read_braced(body, _skip_space(body, i))
        props.append((number.strip(), text))
    return props


NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")


def parent(number: str) -> str | None:
    """Wittgenstein's `x.0n` remarks sit under a label-only `x.0` group, which sits under `x`."""
    if "." not in number:
        return None
    head, _, frac = number[:-1].partition(".")
    if frac == "":
        return head
    if set(frac) == {"0"}:
        return f"{head}.0"
    return number[:-1].rstrip("0").rstrip(".")


def is_group(number: str) -> bool:
    return number.endswith(".0")


# ── tree ──────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Text:
    value: str  # literal characters; typography (``, --, ~) is applied by the serializer


@dataclass(frozen=True)
class Math:
    children: Nodes  # $…$


@dataclass(frozen=True)
class Group:
    children: Nodes  # {…}


@dataclass(frozen=True)
class Cmd:
    name: str
    args: tuple[Nodes, ...]
    opt: Nodes | None


@dataclass(frozen=True)
class Env:
    name: str
    spec: str | None
    children: Nodes


@dataclass(frozen=True)
class ParBreak:
    pass  # blank line


@dataclass(frozen=True)
class Align:
    pass  # &


type Node = Text | Math | Group | Cmd | Env | ParBreak | Align
type Nodes = tuple[Node, ...]


# ── command table ─────────────────────────────────────────────────────────────


class _InMath:
    def __repr__(self) -> str:
        return "IN_MATH"


IN_MATH = _InMath()
"""Text-mode marker: the serializer switches into math and uses the `math` handler."""

type TextHandler = Callable[[Sink, Cmd], None]
type MathHandler = Callable[[Emitter, Cmd], str]


@dataclass(frozen=True)
class CommandSpec:
    nargs: int
    optional: bool
    text: TextHandler | _InMath | None
    math: MathHandler | None
    # How each argument is read: "text" or "math" (parsed in that mode), "same" (the mode the
    # command appears in), or "raw" (a dimension or file name, kept as one Text node).
    argmodes: tuple[str, ...] = ()
    optmode: str = "raw"

    def argmode(self, k: int) -> str:
        return self.argmodes[k] if k < len(self.argmodes) else "same"


def _nothing_text(sink: Sink, cmd: Cmd) -> None:
    return None


def _nothing_math(em: Emitter, cmd: Cmd) -> str:
    return ""


def _emph_text(sink: Sink, cmd: Cmd) -> None:
    sink.emph(cmd.args[0])


def _textit_math(em: Emitter, cmd: Cmd) -> str:
    return em.mathtext(cmd.args[0], "\\textit")


def _abbrev(word: str) -> TextHandler:
    return lambda sink, cmd: sink.emph((Text(word),))


def _last_arg_text(sink: Sink, cmd: Cmd) -> None:
    sink.nodes(cmd.args[-1])


def _text_math(em: Emitter, cmd: Cmd) -> str:
    return em.mathtext(cmd.args[-1], "\\text")


def _chars(s: str) -> TextHandler:
    return lambda sink, cmd: sink.chars(s, plain=True)


def _const(tex: str) -> MathHandler:
    return lambda em, cmd: tex


def _unchanged(em: Emitter, cmd: Cmd) -> str:
    """The command and its braced arguments, as written."""
    head = "~" if cmd.name == "~" else "\\" + cmd.name
    return em.join([head, *("{" + em.math(a) + "}" for a in cmd.args)])


def _not_math(em: Emitter, cmd: Cmd) -> str:
    return em.join(["\\sim ", em.math(cmd.args[0])])


def _typo_text(sink: Sink, cmd: Cmd) -> None:
    sink.nodes(cmd.args[1])


def _typo_math(em: Emitter, cmd: Cmd) -> str:
    return em.math(cmd.args[1])


def _ref_text(sink: Sink, cmd: Cmd) -> None:
    number = _raw(cmd.args[0])
    if NUMBER_RE.fullmatch(number) is None:
        raise ConversionError(sink.ctx.number, f"bad \\PropERef target {number!r}")
    sink.link(number, "#" + number)


def _footnote_text(sink: Sink, cmd: Cmd) -> None:
    sink.note(cmd.args[0])


def _illustration_text(sink: Sink, cmd: Cmd) -> None:
    sink.par()
    sink.emph((Text(f"Figure omitted: {Path(_raw(cmd.args[0])).stem}"),))
    sink.par()


def _raw(nodes: Nodes) -> str:
    (node,) = nodes or (Text(""),)
    assert isinstance(node, Text)
    return node.value.strip()


def _math_word(name: str, nargs: int = 0) -> tuple[str, CommandSpec]:
    return name, CommandSpec(nargs, False, IN_MATH, _unchanged, ("math",) * nargs)


NOTHING = CommandSpec(0, False, _nothing_text, _nothing_math)

COMMANDS: dict[str, CommandSpec] = {
    # emphasis
    **{
        name: CommandSpec(1, False, _emph_text, _textit_math, ("text",))
        for name in ("emph", "textit", "BookTitle", "German", "Emph", "EmphPart")
    },
    "idEst": CommandSpec(0, False, _abbrev("i.e."), None),
    "IdEst": CommandSpec(0, False, _abbrev("I.e."), None),
    "exempliGratia": CommandSpec(0, False, _abbrev("e.g."), None),
    "ExempliGratia": CommandSpec(0, False, _abbrev("E.g."), None),
    # the book's logical operators
    "Not": CommandSpec(1, False, IN_MATH, _not_math, ("math",)),
    "DotOp": CommandSpec(0, False, IN_MATH, _const("\\mathbin{.}")),
    "BarOp": CommandSpec(0, False, IN_MATH, _const("\\mathbin{\\vert}")),
    "Implies": CommandSpec(0, False, IN_MATH, _const("\\supset")),
    "fourdots": CommandSpec(0, False, IN_MATH, _const("\\ldotp" * 4)),
    "fivedots": CommandSpec(0, False, IN_MATH, _const("\\ldotp" * 5)),
    "DittoInWords": CommandSpec(0, False, _chars("〃 〃"), None),
    # structure
    "PropERef": CommandSpec(1, False, _ref_text, None, ("raw",)),
    "DPtypo": CommandSpec(2, False, _typo_text, _typo_math),
    "footnote": CommandSpec(1, False, _footnote_text, None, ("text",)),
    "Illustration": CommandSpec(1, True, _illustration_text, None, ("raw",)),
    # layout only
    "Strut": CommandSpec(0, True, _nothing_text, _nothing_math),
    "stretchyspace": NOTHING,
    "verystretchyspace": NOTHING,
    "AllowBreak": NOTHING,
    "footnotesize": NOTHING,
    "noindent": NOTHING,
    "centering": NOTHING,
    "enlargethispage": CommandSpec(1, False, _nothing_text, _nothing_math, ("raw",)),
    "phantom": CommandSpec(1, False, _nothing_text, _nothing_math),
    # \smash[t]{x} typesets x with zero height: its content is kept.
    "smash": CommandSpec(1, True, _last_arg_text, _unchanged),
    "hspace": CommandSpec(1, False, _chars(" "), None, ("raw",)),
    # boxes
    "mbox": CommandSpec(1, False, _last_arg_text, _text_math, ("text",)),
    "raisebox": CommandSpec(2, False, _last_arg_text, _text_math, ("raw", "text")),
    "text": CommandSpec(1, False, _last_arg_text, _text_math, ("text",)),
    # control symbols
    **{c: CommandSpec(0, False, _chars(c), _unchanged) for c in "%&$_#"},
    "{": CommandSpec(0, False, _chars("{"), _unchanged),
    "}": CommandSpec(0, False, _chars("}"), _unchanged),
    ";": CommandSpec(0, False, _chars(" "), _unchanged),
    ",": CommandSpec(0, False, _nothing_text, _unchanged),
    "!": CommandSpec(0, False, _nothing_text, _unchanged),
    " ": CommandSpec(0, False, _chars(" "), _unchanged),
    "~": CommandSpec(0, False, _chars(" "), _unchanged),
    "-": CommandSpec(0, False, _nothing_text, None),  # discretionary hyphen
    # Line break: markdown paragraphs have no hard breaks, so a space in text mode.
    "\\": CommandSpec(0, False, _chars(" "), _unchanged),
    "hline": CommandSpec(0, False, None, _unchanged),
    # math vocabulary (MathJax base and ams)
    **dict(
        _math_word(name)
        for name in (
            "supset", "sim", "vert", "ldotp", "ldots", "lor", "exists", "equiv", "times",
            "vdash", "sum", "limits", "aleph", "flat", "sharp",
            "Omega", "xi", "phi", "nu", "eta", "mu", "kappa", "psi",
        )
    ),
    **dict(_math_word(name, 1) for name in ("mathbin", "overline", "bar")),
    **dict(_math_word(name, 2) for name in ("binom", "frac")),
}

# Environment -> (optional argument?, column spec?, mode of its children, direct `&` allowed?)
ENVIRONMENTS: dict[str, tuple[bool, bool, str, bool]] = {
    "tabular": (True, True, "text", True),
    "array": (True, True, "math", True),
    "gather*": (False, False, "math", False),
    "split": (False, False, "math", False),
    "center": (False, False, "text", False),
    "table*": (True, False, "text", False),
}
DISPLAY = "displaymath"  # \[ … \], an internal name: parsed like an environment in math mode
MATH_ENVS = {"array": "array", "gather*": "gathered", "split": "aligned"}


# ── parser ────────────────────────────────────────────────────────────────────


class _Parser:
    def __init__(self, number: str, s: str):
        self.number = number
        self.s = s
        self.i = 0

    def fail(self, message: str) -> ConversionError:
        return ConversionError(self.number, message)

    def peek(self, k: int = 0) -> str:
        j = self.i + k
        return self.s[j] if j < len(self.s) else ""

    def skip_arg_space(self) -> None:
        """TeX skips spaces (and a single newline, but not a blank line) before arguments."""
        m = re.compile(r"[ \t]*(?:\n[ \t]*)?").match(self.s, self.i)
        if m is not None and "\n" not in self.s[m.end() : m.end() + 1]:
            self.i = m.end()

    def nodes(self, mode: str, until: str | None, align: bool = False) -> Nodes:
        out: list[Node] = []
        text: list[str] = []

        def flush() -> None:
            if text:
                out.append(Text("".join(text)))
                text.clear()

        def add(node: Node) -> None:
            flush()
            out.append(node)

        while self.i < len(self.s):
            c = self.s[self.i]
            if c in " \t\n":
                m = re.compile(r"[ \t\n]+").match(self.s, self.i)
                self.i = m.end()
                if m.group(0).count("\n") >= 2:
                    if mode == "math":
                        raise self.fail("blank line in math")
                    add(ParBreak())
                else:
                    text.append(m.group(0))
            elif c == "\\":
                if self.s.startswith("\\end", self.i) and not self.peek(4).isalpha():
                    self.i += 4
                    name, self.i = read_braced(self.s, self.i)
                    if until != "end:" + name:
                        raise self.fail(f"unexpected \\end{{{name}}}")
                    flush()
                    return tuple(out)
                if self.s.startswith("\\]", self.i):
                    self.i += 2
                    if until != "\\]":
                        raise self.fail("unexpected \\]")
                    flush()
                    return tuple(out)
                add(self.control(mode))
            elif c == "{":
                self.i += 1
                add(Group(self.nodes(mode, "}")))
            elif c == "}":
                self.i += 1
                if until != "}":
                    raise self.fail("unbalanced }")
                flush()
                return tuple(out)
            elif c == "]" and until == "]":
                self.i += 1
                flush()
                return tuple(out)
            elif c == "$":
                self.i += 1
                if mode == "math":
                    if until != "$":
                        raise self.fail("$ inside a math group")
                    flush()
                    return tuple(out)
                if self.peek() == "$":
                    raise self.fail("$$ display math is not supported")
                add(Math(self.nodes("math", "$")))
            elif c == "&":
                self.i += 1
                if not align:
                    raise self.fail("& outside tabular or array")
                add(Align())
            elif c == "~":
                self.i += 1
                add(Cmd("~", (), None))
            elif c in "#%":
                raise self.fail(f"raw {c!r}")
            else:
                self.i += 1
                text.append(c)
        if until is not None:
            raise self.fail(f"unterminated input (expected {until})")
        flush()
        return tuple(out)

    def control(self, mode: str) -> Node:
        """Parse a control sequence at self.i (a `\\`)."""
        self.i += 1
        m = re.compile(r"[A-Za-z]+").match(self.s, self.i)
        if m is not None:
            name = m.group(0)
            self.i = m.end()
            # TeX drops spaces after a control word (a blank line still ends the paragraph).
            # Math ignores spaces anyway, so there they are kept for readable TeX.
            ws = re.compile(r"[ \t\n]*").match(self.s, self.i).group(0)
            if ws.count("\n") < 2 and mode != "math":
                self.i += len(ws)
        elif self.i < len(self.s):
            name = self.s[self.i]
            self.i += 1
            if name == "\n":
                name = " "
        else:
            raise self.fail("trailing backslash")
        if name == "begin":
            return self.environment(mode)
        if name == "[":
            if mode == "math":
                raise self.fail("\\[ inside math")
            return Env(DISPLAY, None, self.nodes("math", "\\]"))
        spec = COMMANDS.get(name)
        if spec is None:
            raise self.fail(f"unknown command \\{name}")
        opt = None
        if spec.optional:
            self.skip_arg_space()
            if self.peek() == "[":
                self.i += 1
                opt = self.arg_body(spec.optmode, mode, "]")
        args = []
        for k in range(spec.nargs):
            self.skip_arg_space()
            argmode = spec.argmode(k)
            c = self.peek()
            if c == "{":
                self.i += 1
                args.append(self.arg_body(argmode, mode, "}"))
            elif c == "\\":
                token = self.control(mode if argmode in ("same", "raw") else argmode)
                if isinstance(token, Cmd) and token.args:
                    raise self.fail(f"\\{name}: unbraced argument \\{token.name} takes arguments")
                args.append((token,))
            elif c and c not in "}$&%# \t\n":
                self.i += 1
                args.append((Text(c),))
            else:
                raise self.fail(f"\\{name}: missing argument")
        return Cmd(name, tuple(args), opt)

    def arg_body(self, argmode: str, mode: str, close: str) -> Nodes:
        if argmode == "raw":
            j = self.s.find(close, self.i)
            if j == -1:
                raise self.fail(f"unterminated argument (expected {close})")
            raw = self.s[self.i : j]
            if any(c in raw for c in "{$&#"):
                raise self.fail(f"unexpected markup in raw argument {raw!r}")
            self.i = j + 1
            return (Text(raw),)
        return self.nodes(mode if argmode == "same" else argmode, close)

    def environment(self, mode: str) -> Env:
        name, self.i = read_braced(self.s, self.i)
        if name not in ENVIRONMENTS:
            raise self.fail(f"unknown environment {name}")
        has_opt, has_spec, child_mode, align = ENVIRONMENTS[name]
        if has_opt and self.peek() == "[":
            j = self.s.find("]", self.i)
            if j == -1:
                raise self.fail(f"{name}: unterminated optional argument")
            self.i = j + 1
        spec = None
        if has_spec:
            self.skip_arg_space()
            spec, self.i = read_braced(self.s, self.i)
        return Env(name, spec, self.nodes(child_mode, "end:" + name, align))


def parse(number: str, raw: str) -> Nodes:
    try:
        return _Parser(number, raw).nodes("text", None)
    except ConversionError as e:
        if e.number is None:
            raise ConversionError(number, e.message) from e
        raise


# ── serializer ────────────────────────────────────────────────────────────────

SYNTAX = "\\`*_$[]"  # the template's SYNTAX: exactly the characters escapeInline escapes
TYPOGRAPHY = (("``", "“"), ("''", "”"), ("`", "‘"), ("'", "’"), ("---", "—"), ("--", "–"))
LIST_MARKER = re.compile(r"^(?:([-+])|(\d+)([.)]))(?= |$)")


def typography(s: str) -> str:
    for a, b in TYPOGRAPHY:
        s = s.replace(a, b)
    return s


def escape_inline(s: str) -> str:
    return "".join("\\" + c if c in SYNTAX else c for c in s)


def collapse(s: str) -> str:
    return re.sub(r"\s+", " ", s)


def _ends_with_control_word(s: str) -> bool:
    m = re.search(r"(\\+)[A-Za-z]+$", s)
    return m is not None and len(m.group(1)) % 2 == 1


class Converted(NamedTuple):
    paragraphs: list[str]
    math: list[str]


@dataclass
class Context:
    number: str
    notes: list[str] = field(default_factory=list)
    math: list[str] = field(default_factory=list)
    note_math: list[str] = field(default_factory=list)


class Emitter:
    """Math mode (bare TeX) and the environment translations; text modes live in the sinks."""

    def __init__(self, ctx: Context):
        self.ctx = ctx

    def fail(self, message: str) -> ConversionError:
        return ConversionError(self.ctx.number, message)

    @staticmethod
    def join(parts: list[str]) -> str:
        """Concatenate TeX so that a control word never runs into a following letter."""
        out = ""
        for p in parts:
            if p and out and p[0].isascii() and p[0].isalpha() and _ends_with_control_word(out):
                out += " "
            out += p
        return out

    def math(self, nodes: Nodes) -> str:
        parts = []
        for node in nodes:
            match node:
                case Text(value):
                    # In TeX math a backquote is an opening-quote glyph; MathJax shows a grave
                    # accent, so emit the quote as text.
                    value = value.replace("``", "\\text{“}").replace("`", "\\text{‘}")
                    parts.append(value)
                case Group(children):
                    parts.append("{" + self.math(children) + "}")
                case Cmd(name):
                    spec = COMMANDS[name]
                    if spec.math is None:
                        raise self.fail(f"\\{name} is not allowed in math")
                    parts.append(spec.math(self, node))
                case Env():
                    parts.append(self.env_math(node))
                case Align():
                    parts.append("&")
                case Math() | ParBreak():
                    raise self.fail(f"{type(node).__name__} inside math")
        return collapse(self.join(parts))

    def mathtext(self, nodes: Nodes, wrapper: str, trim: bool = False) -> str:
        sink = MathtextSink(self)
        sink.nodes(nodes)
        return sink.render(wrapper, trim)

    def env_math(self, env: Env) -> str:
        if env.name == "tabular":
            return self.tabular(env)
        if env.name not in MATH_ENVS:
            raise self.fail(f"environment {env.name} is not allowed in math")
        name = MATH_ENVS[env.name]
        spec = "" if env.spec is None else "{" + self.column_spec(env.spec) + "}"
        return self.join([f"\\begin{{{name}}}{spec}", self.math(env.children), f"\\end{{{name}}}"])

    def column_spec(self, spec: str) -> str:
        # MathJax 3.2.2 reads only c, l, r, | and : from a column spec; @{…} is dropped here
        # rather than passed through as markup that has no effect.
        cols = re.sub(r"@\{[^{}]*\}", "", spec).replace(" ", "")
        if re.fullmatch(r"[clr|]+", cols) is None:
            raise self.fail(f"unsupported column spec {spec!r}")
        return cols

    def tabular(self, env: Env) -> str:
        """tabular -> array; cell text becomes \\text{…}, math in cells stays math."""
        parts: list[str] = []
        cell: list[Node] = []

        def flush() -> None:
            parts.append(self.mathtext(tuple(cell), "\\text", trim=True))
            cell.clear()

        for node in env.children:
            if isinstance(node, Align):
                flush()
                parts.append(" & ")
            elif isinstance(node, Cmd) and node.name == "\\":
                flush()
                parts.append(" \\\\ ")
            elif isinstance(node, Cmd) and node.name == "hline":
                flush()
                parts.append("\\hline")
            else:
                cell.append(node)
        flush()
        body = collapse(self.join(parts)).strip()
        spec = self.column_spec(env.spec or "")
        return self.join([f"\\begin{{array}}{{{spec}}}", body, "\\end{array}"])


class Sink:
    """A text-mode target. Text handlers write through this interface only."""

    def __init__(self, em: Emitter):
        self.em = em
        self.ctx = em.ctx

    def fail(self, message: str) -> ConversionError:
        return self.em.fail(message)

    def nodes(self, nodes: Nodes) -> None:
        for node in nodes:
            match node:
                case Text(value):
                    self.chars(value)
                case Math(children):
                    self.math(self.em.math(children))
                case Group(children):
                    self.nodes(children)
                case Cmd(name):
                    spec = COMMANDS[name]
                    if spec.text is None:
                        raise self.fail(f"\\{name} is not allowed in text")
                    if spec.text is IN_MATH:
                        self.math(spec.math(self.em, node))
                    else:
                        spec.text(self, node)
                case Env():
                    self.env(node)
                case ParBreak():
                    self.par()
                case Align():
                    raise self.fail("& outside tabular or array")

    def chars(self, s: str, plain: bool = False) -> None: ...
    def math(self, tex: str) -> None: ...
    def emph(self, nodes: Nodes) -> None: ...
    def link(self, label: str, dest: str) -> None: ...
    def note(self, nodes: Nodes) -> None: ...
    def par(self) -> None: ...
    def env(self, env: Env) -> None: ...


class MarkdownSink(Sink):
    """Text mode: markdown under the template's inline grammar."""

    def __init__(self, em: Emitter, in_emph: bool = False):
        super().__init__(em)
        self.in_emph = in_emph
        self.paragraphs: list[str] = []
        self.cur: list[str] = []
        self.mathbuf: list[str] | None = None
        self.after_math = False

    def _put(self, piece: str) -> None:
        self._close_math()
        if piece and self.after_math:
            # The grammar does not close a span before a digit.
            if piece[0] in "0123456789":
                raise self.fail(f"math span followed by digit: {piece[:20]!r}")
            self.after_math = False
        self.cur.append(piece)

    def _close_math(self) -> None:
        if self.mathbuf is None:
            return
        tex = collapse(self.em.join(self.mathbuf)).strip()
        self.mathbuf = None
        # A trailing control space would leave `\` before the closing `$`.
        while re.search(r"(?<!\\)(?:\\\\)*\\$", tex):
            tex = tex[:-1].rstrip()
        if tex:
            self.ctx.math.append(tex)
            self.cur.append(f"${tex}$")
            self.after_math = True

    def chars(self, s: str, plain: bool = False) -> None:
        self._put(escape_inline(s if plain else typography(s)))

    def math(self, tex: str) -> None:
        if self.mathbuf is None:
            self.mathbuf = []
        self.mathbuf.append(tex)

    def emph(self, nodes: Nodes) -> None:
        if self.in_emph:
            self.nodes(nodes)
            return
        sub = MarkdownSink(self.em, in_emph=True)
        sub.nodes(nodes)
        content = sub.inline()
        stripped = content.strip()
        if not stripped:
            self._put(" " if content else "")
            return
        lead = " " if content[0].isspace() else ""
        trail = " " if content[-1].isspace() else ""
        self._put(f"{lead}*{stripped}*{trail}")

    def link(self, label: str, dest: str) -> None:
        self._put(f"[{escape_inline(label)}]({dest})")

    def note(self, nodes: Nodes) -> None:
        ctx = Context(self.ctx.number, self.ctx.notes)
        sub = MarkdownSink(Emitter(ctx))
        sub.nodes(nodes)
        paragraphs = sub.finish()
        if len(paragraphs) != 1:
            raise self.fail("a footnote must be one paragraph")
        self.ctx.notes.append(paragraphs[0])
        self.ctx.note_math.extend(ctx.math + ctx.note_math)

    def par(self) -> None:
        self._close_math()
        text = collapse("".join(self.cur)).strip()
        self.cur = []
        self.after_math = False
        if text:
            m = LIST_MARKER.match(text)
            if m is not None:
                text = ("\\" + m.group(1) if m.group(1) else m.group(2) + "\\" + m.group(3)) + text[m.end() :]
            self.paragraphs.append(text)

    def block_math(self, tex: str) -> None:
        self.par()
        self.math(tex)
        self.par()

    def env(self, env: Env) -> None:
        if env.name in ("center", "table*"):
            self.par()
            self.nodes(env.children)
            self.par()
        elif env.name == DISPLAY:
            self.block_math(self.em.math(env.children))
        else:
            self.block_math(self.em.env_math(env))

    def inline(self) -> str:
        """The content of an inline context such as emphasis; paragraph breaks are errors."""
        self._close_math()
        if self.paragraphs:
            raise self.fail("paragraph break inside an inline argument")
        return collapse("".join(self.cur))

    def finish(self) -> list[str]:
        self.par()
        return self.paragraphs


class MathtextSink(Sink):
    """Inside \\text{…} in math: typography, no markdown; math children close the text group."""

    def __init__(self, em: Emitter):
        super().__init__(em)
        self.pieces: list[tuple[str, str]] = []

    def chars(self, s: str, plain: bool = False) -> None:
        s = s if plain else typography(s)
        # MathJax's text mode reads `$` as math and un-escapes \$, \{, \} and \\.
        self.pieces.append(("text", re.sub(r"([\\${}])", r"\\\1", s)))

    def math(self, tex: str) -> None:
        self.pieces.append(("math", tex))

    def emph(self, nodes: Nodes) -> None:
        self.nodes(nodes)

    def link(self, label: str, dest: str) -> None:
        self.chars(label, plain=True)

    def note(self, nodes: Nodes) -> None:
        raise self.fail("\\footnote inside math")

    def par(self) -> None:
        raise self.fail("paragraph break inside math text")

    def env(self, env: Env) -> None:
        raise self.fail(f"environment {env.name} inside math text")

    def render(self, wrapper: str, trim: bool) -> str:
        runs: list[tuple[str, str]] = []
        for kind, s in self.pieces:
            if runs and runs[-1][0] == kind == "text":
                runs[-1] = ("text", runs[-1][1] + s)
            else:
                runs.append((kind, s))
        if trim and runs and runs[0][0] == "text":
            runs[0] = ("text", runs[0][1].lstrip())
        if trim and runs and runs[-1][0] == "text":
            runs[-1] = ("text", runs[-1][1].rstrip())
        out = []
        for kind, s in runs:
            if kind == "math":
                out.append(s)
            elif collapse(s).strip():
                out.append(f"{wrapper}{{{collapse(s)}}}")
        return self.em.join(out)


def convert(number: str, raw: str) -> Converted:
    ctx = Context(number)
    sink = MarkdownSink(Emitter(ctx))
    sink.nodes(parse(number, raw))
    paragraphs = sink.finish() + [f"Note: {n}" for n in ctx.notes]
    return Converted(paragraphs, ctx.math + ctx.note_math)


# ── output ────────────────────────────────────────────────────────────────────


def depth(number: str) -> int:
    p = parent(number)
    return 1 if p is None else 1 + depth(p)


def build_markdown(props: list[tuple[str, str]]) -> str:
    if len(props) != EXPECTED_PROPOSITIONS:
        raise ConversionError(None, f"expected {EXPECTED_PROPOSITIONS} propositions, found {len(props)}")
    lines = [TITLE, "", INTRO, ""]
    seen: set[str] = set()
    for number, raw in props:
        if NUMBER_RE.fullmatch(number) is None:
            raise ConversionError(number, "malformed proposition number")
        if number in seen:
            raise ConversionError(number, "duplicate proposition number")
        p = parent(number)
        if p is not None and p not in seen and is_group(p):
            lines.append(f"{'  ' * (depth(p) - 1)}- {p}")
            seen.add(p)
        if p is not None and p not in seen:
            raise ConversionError(number, f"parent {p} was not emitted earlier")
        seen.add(number)
        paragraphs = convert(number, raw).paragraphs
        if not paragraphs:
            raise ConversionError(number, "empty proposition")
        indent = "  " * (depth(number) - 1)
        lines.append(f"{indent}- {number} {paragraphs[0]}")
        for para in paragraphs[1:]:
            lines += ["", f"{indent}  {para}"]
    return "\n".join(lines) + "\n"


def _download() -> bytes:
    request = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "build_tractatus.py"})
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "5740-t.tex"
        with urllib.request.urlopen(request, timeout=60) as response:
            path.write_bytes(response.read())
        return path.read_bytes()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--source", help="local copy of the TeX source (default: download)")
    parser.add_argument("--out-dir", default=str(HERE))
    parser.add_argument("--print-sha256", action="store_true")
    args = parser.parse_args(argv)
    data = Path(args.source).read_bytes() if args.source else _download()
    if args.print_sha256:
        print(hashlib.sha256(data).hexdigest())
        return 0
    try:
        props = extract_propositions(load_source(data))
        markdown = build_markdown(props)
    except ConversionError as e:
        print(f"build_tractatus.py: {e}", file=sys.stderr)
        return 1
    out = Path(args.out_dir)
    (out / "tractatus.md").write_text(markdown, encoding="utf-8", newline="")
    page = embed.embed(markdown, embed.TEMPLATE.read_bytes().decode("utf-8"))
    (out / "tractatus.html").write_text(page, encoding="utf-8", newline="")
    print(f"{len(props)} propositions, max depth {max(depth(n) for n, _ in props)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
