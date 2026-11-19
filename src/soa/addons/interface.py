"""Add-on manifest and hook protocol.

Hooks an add-on may implement:

- ``before_plan(plan, context)`` — inspect or replace a plan
- ``after_plan(plan, report, context)`` — inspect or replace a run report
- ``before_step(step, context)`` — inspect or replace a step
- ``after_step(step, result, context)`` — inspect or replace a step result
- ``on_error(step, error, context)`` — observe a failed step
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

KNOWN_HOOKS = (
    "before_plan",
    "after_plan",
    "before_step",
    "after_step",
    "on_error",
)


@dataclass(frozen=True)
class AddonManifest:
    """Declared metadata for an add-on."""

    name: str
    version: str
    description: str = ""
    hooks: tuple[str, ...] = ("before_step", "after_step")
    author: str = ""

    def __post_init__(self) -> None:
        unknown = [hook for hook in self.hooks if hook not in KNOWN_HOOKS]
        if unknown:
            raise ValueError(f"unknown add-on hooks: {', '.join(unknown)}")


@dataclass
class HookContext:
    """State passed to add-on hooks during a run."""

    goal: str
    extras: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class Addon(Protocol):
    """An optional plug-in loaded beside the core, never into it."""

    manifest: AddonManifest

    def before_plan(self, plan: Any, context: HookContext) -> Any: ...

    def after_plan(self, plan: Any, report: Any, context: HookContext) -> Any: ...

    def before_step(self, step: Any, context: HookContext) -> Any: ...

    def after_step(self, step: Any, result: Any, context: HookContext) -> Any: ...

    def on_error(self, step: Any, error: BaseException, context: HookContext) -> None: ...
