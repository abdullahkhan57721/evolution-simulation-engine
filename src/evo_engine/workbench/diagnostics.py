"""Shared Workbench-owned diagnostics without replacing lower validation authority."""

from __future__ import annotations

from typing import Literal

import attrs

DiagnosticSeverity = Literal["error", "warning"]
ReadinessState = Literal["draft", "blocked", "ready"]

EXACT_REPRODUCTION_REMEDIATION = (
    "Use a compatible recipe/compiler/software implementation for exact reproduction, "
    "or create a new Study revision under the current implementation. Do not treat "
    "re-resolution of old intent as exact reproduction."
)


@attrs.frozen(slots=True, kw_only=True)
class WorkbenchDiagnostic:
    """Describe one Workbench-owned user-facing problem or advisory."""

    code: str
    message: str
    severity: DiagnosticSeverity = "error"
    slot_id: str | None = None
    context: str | None = None
    remediation: str | None = None

    def __attrs_post_init__(self) -> None:
        _require_nonempty(self.code, name="code")
        _require_nonempty(self.message, name="message")
        if self.severity not in ("error", "warning"):
            raise ValueError("severity must be error or warning.")
        if self.slot_id is not None:
            _require_nonempty(self.slot_id, name="slot_id")
        if self.context is not None:
            _require_nonempty(self.context, name="context")
        if self.remediation is not None:
            _require_nonempty(self.remediation, name="remediation")


@attrs.frozen(slots=True, kw_only=True)
class WorkbenchReadiness:
    """Report the small blocking Workbench authoring readiness state."""

    state: ReadinessState
    diagnostics: tuple[WorkbenchDiagnostic, ...] = ()

    def __attrs_post_init__(self) -> None:
        if self.state not in ("draft", "blocked", "ready"):
            raise ValueError("state must be draft, blocked, or ready.")
        if type(self.diagnostics) is not tuple:
            raise TypeError("diagnostics must be a tuple.")
        if any(not isinstance(item, WorkbenchDiagnostic) for item in self.diagnostics):
            raise TypeError("diagnostics entries must be WorkbenchDiagnostic values.")
        if any(item.severity != "error" for item in self.diagnostics):
            raise ValueError("readiness diagnostics must be blocking errors.")
        if self.state == "ready" and self.diagnostics:
            raise ValueError("ready Workbench state must not contain diagnostics.")
        if self.state != "ready" and not self.diagnostics:
            raise ValueError("draft or blocked Workbench state requires diagnostics.")


class WorkbenchNotReadyError(ValueError):
    """Raised when resolution is requested for Draft or Blocked authoring state."""

    def __init__(self, readiness: WorkbenchReadiness) -> None:
        if not isinstance(readiness, WorkbenchReadiness):
            raise TypeError("readiness must be a WorkbenchReadiness value.")
        if readiness.state == "ready":
            raise ValueError("WorkbenchNotReadyError requires non-ready state.")
        self.readiness = readiness
        super().__init__(f"Workbench study is {readiness.state}.")


class IncompatibleManifestError(ValueError):
    """Expose structured remediation when exact saved-manifest reproduction fails."""

    def __init__(
        self,
        message: str,
        *,
        context: str | None = None,
        remediation: str = EXACT_REPRODUCTION_REMEDIATION,
    ) -> None:
        _require_nonempty(message, name="message")
        self.diagnostic = WorkbenchDiagnostic(
            code="exact-reproduction-unavailable",
            message=message,
            context=context,
            remediation=remediation,
        )
        super().__init__(message)


def _require_nonempty(value: object, *, name: str) -> str:
    if type(value) is not str or not value.strip():
        raise TypeError(f"{name} must be a non-empty string.")
    return value


__all__ = [
    "DiagnosticSeverity",
    "EXACT_REPRODUCTION_REMEDIATION",
    "IncompatibleManifestError",
    "ReadinessState",
    "WorkbenchDiagnostic",
    "WorkbenchNotReadyError",
    "WorkbenchReadiness",
]
