"""oauth_cli backend registration (Phase 2).

STUB STATE: signatures only; raises NotImplementedError.
FUTURE (Phase 2): register an `oauth_cli` backend with upstream SkillOpt and force
rollout / reflect / judge through the `OAuthCLIExecutor`, never the provider chat API.
"""
from __future__ import annotations

from .executor import OAuthCLIExecutor


def register_oauth_backend(executor: "OAuthCLIExecutor") -> None:
    """Register the `oauth_cli` backend and bind rollout/reflect/judge to `executor`."""
    raise NotImplementedError("register_oauth_backend is implemented in Phase 2")
