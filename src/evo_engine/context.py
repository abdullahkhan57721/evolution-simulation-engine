"""Typed immutable configuration shared across simulation state snapshots."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Generic, TypeVar, cast, overload

import attrs

T = TypeVar("T")
D = TypeVar("D")


@attrs.frozen(slots=True, kw_only=True)
class ContextKey(Generic[T]):
    """Define a typed key for one immutable simulation-context service.

    ``T`` describes the statically returned service type. ``value_type`` is the
    runtime ``isinstance`` validator and intentionally accepts structural,
    runtime-checkable protocol classes as well as concrete classes.
    """

    name: str
    value_type: type[Any]

    def __attrs_post_init__(self) -> None:
        """Validate key identity and runtime value type."""
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
class _ContextValue:
    """Bind one internal service name to its configured value."""

    name: str
    value: object = attrs.field(repr=False)

    def __attrs_post_init__(self) -> None:
        """Validate the internal service identifier."""
        if type(self.name) is not str:
            raise TypeError("context service names must be strings.")
        if not self.name.strip():
            raise ValueError("context service names must not be blank.")


@attrs.frozen(slots=True, kw_only=True)
class SimulationContext:
    """Hold immutable domain configuration shared by all state snapshots.

    Construct an empty context directly or use :meth:`from_mapping` to bind
    named services. The storage representation is intentionally private so it
    may change without expanding the public kernel API. Successful typed
    lookups are memoized internally because the bound services cannot change.
    """

    _values: tuple[_ContextValue, ...] = attrs.field(
        factory=tuple,
        init=False,
        repr=False,
        validator=attrs.validators.instance_of(tuple),
    )
    _typed_cache: dict[ContextKey[Any], object] = attrs.field(
        factory=dict,
        init=False,
        repr=False,
        eq=False,
    )

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> SimulationContext:
        """Build a context from named domain configuration values."""
        context = cls()
        object.__setattr__(
            context,
            "_values",
            tuple(
                _ContextValue(name=name, value=value) for name, value in values.items()
            ),
        )
        attrs.validate(context)
        return context

    @overload
    def require(self, key: ContextKey[T]) -> T: ...

    @overload
    def require(self, key: str) -> Any: ...

    def require(self, key: str | ContextKey[T]) -> Any | T:
        """Return a required domain configuration service."""
        typed_key = key if isinstance(key, ContextKey) else None
        if typed_key is not None:
            try:
                return cast(T, self._typed_cache[typed_key])
            except KeyError:
                pass

        name = typed_key.name if typed_key is not None else key
        if type(name) is not str:
            raise TypeError("context service name must be a string.")
        if not name.strip():
            raise ValueError("context service name must not be blank.")
        for item in self._values:
            if item.name == name:
                if typed_key is not None:
                    value = typed_key.validate(item.value)
                    self._typed_cache[typed_key] = value
                    return value
                return item.value
        raise KeyError(f"simulation context does not provide {name!r}.")

    @overload
    def get(self, key: ContextKey[T], default: None = None) -> T | None: ...

    @overload
    def get(self, key: ContextKey[T], default: D) -> T | D: ...

    @overload
    def get(self, key: str, default: Any = None) -> Any: ...

    def get(
        self,
        key: str | ContextKey[T],
        default: D | None = None,
    ) -> Any | T | D | None:
        """Return an optional domain configuration service."""
        try:
            return self.require(key)
        except KeyError:
            return default


__all__ = [
    "ContextKey",
    "SimulationContext",
]
