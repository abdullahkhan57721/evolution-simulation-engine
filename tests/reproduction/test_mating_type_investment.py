"""Tests for mating-type-specific parental investment scaling."""

from __future__ import annotations

import pytest

from evo_engine.genetics import OFFSPRING_ENERGY
from evo_engine.reproduction import (
    FixedEnergyInvestment,
    GeneticPhenotypeEnergyInvestment,
    MatingTypeInvestmentScale,
    MatingTypeScaledInvestment,
)
from tests.helpers import make_integer_architecture, make_organism, make_state


def _scale(
    mating_type: str, numerator: int, denominator: int = 1
) -> MatingTypeInvestmentScale:
    return MatingTypeInvestmentScale(
        mating_type=mating_type,
        numerator=numerator,
        denominator=denominator,
    )


def test_mating_type_scaled_investment_follows_parent_identity_not_order() -> None:
    """Test asymmetric investment follows mating type when parent order changes."""
    state = make_state()
    alpha = make_organism(mating_type="alpha")
    beta = make_organism(mating_type="beta")
    model = MatingTypeScaledInvestment(
        base_investment=FixedEnergyInvestment(amount=4),
        scales=(
            _scale("alpha", 3, 2),
            _scale("beta", 1, 2),
        ),
    )

    assert model.determine_investments(
        (alpha, beta),
        simulation_state=state,
    ) == (6, 2)
    assert model.determine_investments(
        (beta, alpha),
        simulation_state=state,
    ) == (2, 6)


def test_unlisted_mating_type_retains_base_investment() -> None:
    """Test unspecified mating types use the neutral one-to-one scale."""
    state = make_state()
    organism = make_organism(mating_type="gamma")
    model = MatingTypeScaledInvestment(
        base_investment=FixedEnergyInvestment(amount=5),
        scales=(_scale("alpha", 2),),
    )

    assert model.determine_investments(
        (organism,),
        simulation_state=state,
    ) == (5,)


def test_mating_type_scale_uses_half_up_integer_rounding() -> None:
    """Test rational scales round exact half units upward deterministically."""
    scale = _scale("alpha", 1, 2)

    assert scale.scale(3) == 2
    assert scale.scale(4) == 2


def test_mating_type_scaled_investment_preserves_nested_trait_requirements() -> None:
    """Test wrapped genetic investment requirements reach engine preflight."""
    model = MatingTypeScaledInvestment(
        base_investment=GeneticPhenotypeEnergyInvestment(),
        scales=(_scale("alpha", 2),),
    )

    assert model.required_traits == frozenset({OFFSPRING_ENERGY})


def test_mating_type_scaled_genetic_investment_uses_each_parent_trait_value() -> None:
    """Test mating-type scaling preserves heritable parent-specific investment."""
    architecture = make_integer_architecture(OFFSPRING_ENERGY)
    state = make_state(genetic_architecture=architecture)
    alpha = make_organism(
        genetic_architecture=architecture,
        trait_values={OFFSPRING_ENERGY: 4},
        mating_type="alpha",
    )
    beta = make_organism(
        genetic_architecture=architecture,
        trait_values={OFFSPRING_ENERGY: 6},
        mating_type="beta",
    )
    model = MatingTypeScaledInvestment(
        base_investment=GeneticPhenotypeEnergyInvestment(),
        scales=(
            _scale("alpha", 3, 2),
            _scale("beta", 1, 2),
        ),
    )

    assert model.determine_investments(
        (alpha, beta),
        simulation_state=state,
    ) == (6, 3)


def test_mating_type_scaled_investment_rejects_duplicate_type_scales() -> None:
    """Test each mating type has at most one configured investment scale."""
    with pytest.raises(ValueError, match="duplicate mating types"):
        MatingTypeScaledInvestment(
            base_investment=FixedEnergyInvestment(amount=4),
            scales=(
                _scale("alpha", 1),
                _scale("alpha", 2),
            ),
        )


def test_mating_type_investment_scale_rejects_blank_label() -> None:
    """Test investment scales require a meaningful mating-type label."""
    with pytest.raises(ValueError, match="mating_type"):
        _scale("   ", 1)
