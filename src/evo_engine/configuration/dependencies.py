"""Collect and validate cross-component simulation dependencies."""

from __future__ import annotations

from collections.abc import Mapping

import attrs

from evo_engine.evolution import CharacteristicRequirementProvider
from evo_engine.genetics import GeneticArchitecture
from evo_engine.genetics.requirements import TraitRequirementProvider
from evo_engine.validation import attrs_validators
from evo_engine.world import WorldState

TRAIT = "trait"
CHARACTERISTIC = "characteristic"
ENVIRONMENTAL_FIELD = "environmental_field"


@attrs.frozen(slots=True, order=True, kw_only=True)
class Dependency:
    """Represent one named capability required or provided by configuration.

    Attributes:
        category: Extensible dependency namespace such as ``trait`` or
            ``environmental_field``.
        name: Name within the dependency namespace.
    """

    category: str = attrs.field(validator=attrs_validators.validate_str)
    name: str = attrs.field(validator=attrs_validators.validate_str)

    def __attrs_post_init__(self) -> None:
        """Reject blank dependency categories and names."""
        if not self.category.strip():
            raise ValueError("dependency category must not be blank.")
        if not self.name.strip():
            raise ValueError("dependency name must not be blank.")


@attrs.frozen(slots=True, kw_only=True)
class DependencyReport:
    """Summarize required, provided, and missing simulation capabilities.

    Attributes:
        required: Capabilities required by configured component objects.
        provided: Capabilities supplied by the configured biological context.
    """

    required: frozenset[Dependency]
    provided: frozenset[Dependency]

    @property
    def missing(self) -> frozenset[Dependency]:
        """Return required capabilities not supplied by the configuration."""
        return self.required - self.provided

    def require_satisfied(self) -> None:
        """Raise if any required simulation capability is unavailable.

        Raises:
            ValueError: If one or more required capabilities are missing.
        """
        if not self.missing:
            return
        formatted = ", ".join(
            f"{dependency.category}:{dependency.name}"
            for dependency in sorted(self.missing)
        )
        raise ValueError(f"simulation configuration has missing dependencies: {formatted}")


def collect_component_dependencies(*components: object) -> frozenset[Dependency]:
    """Recursively collect declared dependencies from a component object graph.

    The collector understands existing genetic-trait requirements, generic
    characteristic requirements, and ``required_environmental_fields``. It
    traverses attrs objects, ordinary configured Python objects, mappings, and
    standard containers. This lets leaf policies declare their own dependencies
    without requiring every coordinator and composite to duplicate declarations.

    Args:
        components: Root configured components to inspect.

    Returns:
        All dependencies declared anywhere below the supplied roots.
    """
    dependencies: set[Dependency] = set()
    seen: set[int] = set()

    for component in components:
        _collect_from_object(component, dependencies=dependencies, seen=seen)

    return frozenset(dependencies)


def provided_biological_dependencies(
    genetic_architecture: GeneticArchitecture,
    world: WorldState,
) -> frozenset[Dependency]:
    """Return capabilities supplied by a biological simulation context.

    Every genetic architecture trait is available both as raw genetic
    expression and, by the development invariant, as a developmental
    characteristic with the same name. World environmental fields provide
    named environmental capabilities.

    Args:
        genetic_architecture: Genetic architecture configured for the run.
        world: Initial world defining named environmental fields.

    Returns:
        Capabilities available to configured components.
    """
    provided: set[Dependency] = set()
    for trait_name in genetic_architecture.trait_names:
        provided.add(Dependency(category=TRAIT, name=trait_name))
        provided.add(Dependency(category=CHARACTERISTIC, name=trait_name))
    for field_name in world.environmental_field_names:
        provided.add(Dependency(category=ENVIRONMENTAL_FIELD, name=field_name))
    return frozenset(provided)


def dependency_report(
    *,
    components: tuple[object, ...],
    genetic_architecture: GeneticArchitecture,
    world: WorldState,
) -> DependencyReport:
    """Build a dependency report for a biological simulation specification.

    Args:
        components: Configured component roots.
        genetic_architecture: Genetic architecture supplying trait capabilities.
        world: Initial world supplying environmental capabilities.

    Returns:
        Dependency report containing required and provided capabilities.
    """
    return DependencyReport(
        required=collect_component_dependencies(*components),
        provided=provided_biological_dependencies(genetic_architecture, world),
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

    _collect_declared_requirements(value, dependencies=dependencies)

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


def _collect_declared_requirements(
    component: object,
    *,
    dependencies: set[Dependency],
) -> None:
    if isinstance(component, TraitRequirementProvider):
        dependencies.update(
            Dependency(category=TRAIT, name=name)
            for name in component.required_traits
        )

    if isinstance(component, CharacteristicRequirementProvider):
        dependencies.update(
            Dependency(category=CHARACTERISTIC, name=name)
            for name in component.required_characteristics
        )

    environmental_fields = getattr(component, "required_environmental_fields", None)
    if environmental_fields is None:
        return
    if type(environmental_fields) is not frozenset:
        raise TypeError(
            f"{type(component).__name__}.required_environmental_fields must be a "
            "frozenset."
        )
    for field_name in environmental_fields:
        if type(field_name) is not str:
            raise TypeError("required environmental field names must be strings.")
        if not field_name.strip():
            raise ValueError("required environmental field names must not be blank.")
        dependencies.add(Dependency(category=ENVIRONMENTAL_FIELD, name=field_name))


def _is_terminal(value: object) -> bool:
    return value is None or type(value) in (str, int, float, bool, bytes, type)
