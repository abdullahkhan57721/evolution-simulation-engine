"""Represent immutable domain-neutral simulation configuration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Generic, TypeVar, cast

import attrs

T = TypeVar("T")


@attrs.frozen(slots=True, kw_only=True)
class ContextKey(Generic[T]):
    """Define a typed key for one immutable simulation-context service."""

    name: str
    value_type: type[T]

    def __attrs_post_init__(self) -> None:
        if type(self.name) is not str:
            raise TypeError("ContextKey.name must be a string.")
        if not self.name.strip():
            raise ValueError("ContextKey.name must not be blank.")
        if not isinstance(self.value_type, type):
            raise TypeError("ContextKey.value_type must be a type.")

    def validate(self, value: object) -> T:
        """Validate and return a value bound to this key."""
        if not isinstance(value, self.value_type):
            raise TypeError(
                f"context value for {self.name!r} must be a {self.value_type.__name__}."
            )
        return cast(T, value)


@attrs.frozen(slots=True, kw_only=True)
class ContextValue:
    """Bind one named immutable configuration service to a simulation context."""

    name: str
    value: object = attrs.field(repr=False)

    def __attrs_post_init__(self) -> None:
        if type(self.name) is not str:
            raise TypeError("ContextValue.name must be a string.")
        if not self.name.strip():
            raise ValueError("ContextValue.name must not be blank.")


@attrs.frozen(slots=True, kw_only=True)
class SimulationContext:
    """Hold immutable domain configuration shared by all state snapshots."""

    values: tuple[ContextValue, ...] = ()

    def __attrs_post_init__(self) -> None:
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
        """Build a context from named domain configuration values."""
        return cls(
            values=tuple(
                ContextValue(name=name, value=value) for name, value in values.items()
            )
        )

    def require(self, key: str | ContextKey[T]) -> Any | T:
        """Return a required domain configuration service."""
        name = key.name if isinstance(key, ContextKey) else key
        if type(name) is not str:
            raise TypeError("context service name must be a string.")
        if not name.strip():
            raise ValueError("context service name must not be blank.")
        for item in self.values:
            if item.name == name:
                if isinstance(key, ContextKey):
                    return key.validate(item.value)
                return item.value
        raise KeyError(f"simulation context does not provide {name!r}.")

    def get(self, key: str | ContextKey[T], default: Any = None) -> Any | T:
        """Return an optional domain configuration service."""
        try:
            return self.require(key)
        except KeyError:
            return default
