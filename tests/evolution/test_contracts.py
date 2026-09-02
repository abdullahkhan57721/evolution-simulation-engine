"""Tests for the general-evolution public contracts."""

from __future__ import annotations

from typing import assert_type

import evo_engine.evolution as evolution_api

from evo_engine.evolution import TransmissibleStateExpression
from evo_engine.genetics import GeneticPhenotype, Genome
from tests.helpers import make_empty_architecture, make_empty_genome


class _IntegerExpression:
    def express(self, value: int) -> str:
        return str(value)


def test_transmissible_state_expression_is_structural() -> None:
    """Test arbitrary expression models can satisfy the generic contract."""
    expression: TransmissibleStateExpression[int, str] = _IntegerExpression()

    result = expression.express(7)

    assert_type(result, str)
    assert result == "7"


def test_biological_expression_keeps_domain_native_parameter_name() -> None:
    """Test biology can expose express(genome) through the generic contract."""
    architecture = make_empty_architecture()
    genome = make_empty_genome()
    expression: TransmissibleStateExpression[Genome, GeneticPhenotype] = architecture

    result = expression.express(genome)

    assert_type(result, GeneticPhenotype)
    assert result == architecture.express(genome)


def test_removed_heritable_state_contracts_are_not_public() -> None:
    """Test the pre-1.0 migration exposes no compatibility aliases."""
    assert not hasattr(evolution_api, "EvolutionaryEntity")
    assert not hasattr(evolution_api, "HeritableStateExpression")
