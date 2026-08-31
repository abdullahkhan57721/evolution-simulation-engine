"""Domain-neutral dependency declarations for simulation configuration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, runtime_checkable

import attrs

from evo_engine.validation import attrs_validators


@attrs.frozen(slots=True, order=True, kw_only=True)
class Dependency:
    """Represent one named capability required or provided by configuration."""

    category: str = attrs.field(validator=attrs_validators.validate_str)
    name: str = attrs.field(validator=attrs_validators.validate_str)

    def __attrs_post_init__(self) -> None:
        if not self.category.strip():
            raise ValueError("dependency category must not be blank.")
        if not self.name.strip():
            raise ValueError("dependency name must not be blank.")


@attrs.frozen(slots=True, kw_only=True)
class DependencyReport:
    """Summarize required, provided, and missing configuration capabilities."""

    required: frozenset[Dependency]
    provided: frozenset[Dependency]

    @property
    def missing(self) -> frozenset[Dependency]:
        """Return required capabilities not supplied by the configuration."""
        return self.required - self.provided

    def require_satisfied(self) -> None:
        """Raise if one or more required capabilities are unavailable."""
        if not self.missing:
            return
        formatted = ", ".join(
            f"{dependency.category}:{dependency.name}"
            for dependency in sorted(self.missing)
        )
        raise ValueError(
            f"simulation configuration has missing dependencies: {formatted}"
        )


@runtime_checkable
class DependencyRequirementProvider(Protocol):
    """Declare domain-neutral capabilities required by one component."""

    @property
    def required_dependencies(self) -> frozenset[Dependency]:
        """Return capabilities required by this component."""
        ...


def collect_component_dependencies(*components: object) -> frozenset[Dependency]:
    """Recursively collect generic dependency declarations from an object graph."""
    dependencies: set[Dependency] = set()
    seen: set[int] = set()
    for component in components:
        _collect_from_object(component, dependencies=dependencies, seen=seen)
    return frozenset(dependencies)


def dependency_report(
    *,
    components: tuple[object, ...],
    required: frozenset[Dependency] = frozenset(),
    provided: frozenset[Dependency] = frozenset(),
) -> DependencyReport:
    """Build a generic dependency report for configured components."""
    return DependencyReport(
        required=collect_component_dependencies(*components) | required,
        provided=provided,
    )


def _collect_from_object(
    value: object,
    *,
    dependencies: set[Dependency],
    seen: set[int],
) -> None:
    if _is_terminal(value):
        return
    identity = id(value)
    if identity in seen:
        return
    seen.add(identity)

    if isinstance(value, DependencyRequirementProvider):
        declared = value.required_dependencies
        if type(declared) is not frozenset:
            raise TypeError(
                f"{type(value).__name__}.required_dependencies must be a frozenset."
            )
        for dependency in declared:
            if not isinstance(dependency, Dependency):
                raise TypeError("required_dependencies entries must be Dependency objects.")
        dependencies.update(declared)

    if attrs.has(type(value)):
        for attribute in attrs.fields(type(value)):
            _collect_from_object(
                getattr(value, attribute.name),
                dependencies=dependencies,
                seen=seen,
            )
        return

    if isinstance(value, Mapping):
        for item in value.values():
            _collect_from_object(item, dependencies=dependencies, seen=seen)
        return

    if isinstance(value, (tuple, list, set, frozenset)):
        for item in value:
            _collect_from_object(item, dependencies=dependencies, seen=seen)
        return

    try:
        attributes = vars(value)
    except TypeError:
        return
    for item in attributes.values():
        _collect_from_object(item, dependencies=dependencies, seen=seen)


def _is_terminal(value: object) -> bool:
    return value is None or type(value) in (str, int, float, bool, bytes, type)
