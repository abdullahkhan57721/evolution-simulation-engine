"""Represent immutable domain-neutral simulation configuration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import attrs


@attrs.frozen(slots=True, kw_only=True)
class ContextValue:
    """Bind one named immutable configuration service to a simulation context.

    Attributes:
        name: Stable namespaced identifier for the configured service.
        value: Domain-defined immutable configuration value.
    """

    name: str
    value: object = attrs.field(repr=False)

    def __attrs_post_init__(self) -> None:
        """Validate the service identifier."""
        if type(self.name) is not str:
            raise TypeError("ContextValue.name must be a string.")
        if not self.name.strip():
            raise ValueError("ContextValue.name must not be blank.")


@attrs.frozen(slots=True, kw_only=True)
class SimulationContext:
    """Hold immutable domain configuration shared by all state snapshots.

    The simulation kernel deliberately assigns no semantics to context values.
    Biological simulations may store a genetic architecture, behavior policy,
    or developmental configuration; another evolutionary domain may store
    entirely different services. The kernel only preserves the values by
    reference across transactional state copies.

    Attributes:
        values: Named immutable domain configuration services.
    """

    values: tuple[ContextValue, ...] = ()

    def __attrs_post_init__(self) -> None:
        """Validate context values and namespaced-key uniqueness."""
        if type(self.values) is not tuple:
            raise TypeError("SimulationContext.values must be a tuple.")

        seen: set[str] = set()
        for index, item in enumerate(self.values):
            if not isinstance(item, ContextValue):
                raise TypeError(
                    f"SimulationContext.values[{index}] must be a ContextValue."
                )
            if item.name in seen:
                raise ValueError(
                    "SimulationContext values must have unique names; "
                    f"duplicate {item.name!r}."
                )
            seen.add(item.name)

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> SimulationContext:
        """Build a context from named domain configuration values.

        Args:
            values: Mapping from stable service names to configuration values.

        Returns:
            Immutable simulation context.
        """
        return cls(
            values=tuple(ContextValue(name=name, value=value) for name, value in values.items())
        )

    def require(self, name: str) -> Any:
        """Return a required domain configuration service.

        Args:
            name: Stable namespaced service identifier.

        Returns:
            Configured service value.

        Raises:
            KeyError: If the requested service is not configured.
        """
        if type(name) is not str:
            raise TypeError("context service name must be a string.")
        if not name.strip():
            raise ValueError("context service name must not be blank.")

        for item in self.values:
            if item.name == name:
                return item.value
        raise KeyError(f"simulation context does not provide {name!r}.")

    def get(self, name: str, default: Any = None) -> Any:
        """Return an optional domain configuration service.

        Args:
            name: Stable namespaced service identifier.
            default: Value returned when the service is absent.

        Returns:
            Configured value or ``default``.
        """
        try:
            return self.require(name)
        except KeyError:
            return default
