"""Tests for canonical trait names and phenotype dependency declarations."""

from __future__ import annotations

import pytest

from evo_engine.genetics import (
    ADULT_BODY_MASS,
    ATTACK_STRENGTH,
    BUILTIN_TRAITS,
    MAX_SPEED,
    OFFSPRING_ENERGY,
    TraitRequirementProvider,
    collect_required_traits,
)
from evo_engine.genetics.requirements import validate_required_traits


def test_builtin_trait_catalog_contains_core_traits() -> None:
    """Test the canonical vocabulary exposes foundational phenotype names."""
    assert ADULT_BODY_MASS in BUILTIN_TRAITS
    assert MAX_SPEED in BUILTIN_TRAITS
    assert OFFSPRING_ENERGY in BUILTIN_TRAITS
    assert ATTACK_STRENGTH in BUILTIN_TRAITS
    assert len(BUILTIN_TRAITS) == 21


def test_builtin_trait_names_are_unique_nonblank_strings() -> None:
    """Test the built-in catalog remains safe for mapping-based phenotypes."""
    assert all(
        type(trait_name) is str and trait_name.strip() for trait_name in BUILTIN_TRAITS
    )


class RequiresSpeed:
    """Test provider declaring one phenotype dependency."""

    @property
    def required_traits(self) -> frozenset[str]:
        """Return a speed dependency."""
        return frozenset({MAX_SPEED})


class RequiresMassAndSpeed:
    """Test provider declaring two phenotype dependencies."""

    @property
    def required_traits(self) -> frozenset[str]:
        """Return mass and speed dependencies."""
        return frozenset({ADULT_BODY_MASS, MAX_SPEED})


def test_trait_requirement_provider_is_structural() -> None:
    """Test custom policies need not inherit from an engine base class."""
    assert isinstance(
        RequiresSpeed(),
        TraitRequirementProvider,
    )


def test_collect_required_traits_unions_providers_and_ignores_others() -> None:
    """Test composed engine components can aggregate policy dependencies."""
    required = collect_required_traits(
        RequiresSpeed(),
        object(),
        RequiresMassAndSpeed(),
    )

    assert required == frozenset(
        {
            ADULT_BODY_MASS,
            MAX_SPEED,
        }
    )


@pytest.mark.parametrize(
    "required_traits",
    [
        {MAX_SPEED},
        (MAX_SPEED,),
        [MAX_SPEED],
    ],
)
def test_required_traits_must_be_frozenset(required_traits) -> None:
    """Test declarations use one immutable representation consistently."""
    with pytest.raises(TypeError):
        validate_required_traits(required_traits)


def test_required_traits_reject_blank_names() -> None:
    """Test dependency declarations cannot contain unusable trait names."""
    with pytest.raises(ValueError):
        validate_required_traits(frozenset({" "}))
