"""Domain-neutral dependency declarations for simulation configuration."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
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
class DependencyRequirement:
    """Record which configured component declared one dependency requirement."""

    dependency: Dependency
    provider_type: str = attrs.field(validator=attrs_validators.validate_str)


@attrs.frozen(slots=True, kw_only=True)
class DependencyReport:
    """Summarize required, provided, and missing configuration capabilities."""

    required: frozenset[Dependency]
    provided: frozenset[Dependency]
    requirements: tuple[DependencyRequirement, ...] = ()

    @property
    def missing(self) -> frozenset[Dependency]:
        """Return required capabilities not supplied by the configuration."""
        return self.required - self.provided

    def require_satisfied(self) -> None:
        """Raise with requirement provenance when capabilities are unavailable."""
        if not self.missing:
            return
        formatted = ", ".join(
            self._format_missing(dependency) for dependency in sorted(self.missing)
        )
        raise ValueError(
            f"simulation configuration has missing dependencies: {formatted}"
        )

    def _format_missing(self, dependency: Dependency) -> str:
        providers = sorted(
            {
                requirement.provider_type
                for requirement in self.requirements
                if requirement.dependency == dependency
            }
        )
        capability = f"{dependency.category}:{dependency.name}"
        if not providers:
            return capability
        return f"{capability} (required by {', '.join(providers)})"


@runtime_checkable
class DependencyRequirementProvider(Protocol):
    """Declare domain-neutral capabilities required by one component."""

    @property
    def required_dependencies(self) -> frozenset[Dependency]:
        """Return capabilities required by this component."""
        ...


def iter_configuration_components(*components: object) -> Iterator[object]:
    """Yield each nonterminal object in a configured component graph once."""
    seen: set[int] = set()
    for component in components:
        yield from _iter_object_graph(component, seen=seen)


def collect_component_dependencies(*components: object) -> frozenset[Dependency]:
    """Recursively collect generic dependency declarations from an object graph."""
    return frozenset(
        requirement.dependency
        for requirement in collect_dependency_requirements(*components)
    )


def collect_dependency_requirements(
    *components: object,
) -> tuple[DependencyRequirement, ...]:
    """Collect dependencies together with the component types that require them."""
    requirements: set[DependencyRequirement] = set()
    for component in iter_configuration_components(*components):
        _collect_declared_requirements(component, requirements=requirements)
    return tuple(
        sorted(requirements, key=lambda item: (item.dependency, item.provider_type))
    )


def dependency_report(
    *,
    components: tuple[object, ...],
    required: frozenset[Dependency] = frozenset(),
    provided: frozenset[Dependency] = frozenset(),
) -> DependencyReport:
    """Build a generic dependency report for configured components."""
    requirements = collect_dependency_requirements(*components)
    return DependencyReport(
        required=frozenset(requirement.dependency for requirement in requirements)
        | required,
        provided=provided,
        requirements=requirements,
    )


def _collect_declared_requirements(
    value: object,
    *,
    requirements: set[DependencyRequirement],
) -> None:
    if not isinstance(value, DependencyRequirementProvider):
        return
    declared = value.required_dependencies
    if type(declared) is not frozenset:
        raise TypeError(
            f"{type(value).__name__}.required_dependencies must be a frozenset."
        )
    provider_type = f"{type(value).__module__}.{type(value).__qualname__}"
    for dependency in declared:
        if not isinstance(dependency, Dependency):
            raise TypeError("required_dependencies entries must be Dependency objects.")
        requirements.add(
            DependencyRequirement(
                dependency=dependency,
                provider_type=provider_type,
            )
        )


def _iter_object_graph(
    value: object,
    *,
    seen: set[int],
) -> Iterator[object]:
    if _is_terminal(value):
        return
    identity = id(value)
    if identity in seen:
        return
    seen.add(identity)

    yield value
    for child in _child_values(value):
        yield from _iter_object_graph(child, seen=seen)


def _child_values(value: object) -> tuple[object, ...]:
    if attrs.has(type(value)):
        return tuple(
            getattr(value, attribute.name) for attribute in attrs.fields(type(value))
        )
    if isinstance(value, Mapping):
        return tuple(value.values())
    if isinstance(value, (tuple, list, set, frozenset)):
        return tuple(value)
    try:
        return tuple(vars(value).values())
    except TypeError:
        return ()


def _is_terminal(value: object) -> bool:
    return value is None or type(value) in (str, int, float, bool, bytes, type)
