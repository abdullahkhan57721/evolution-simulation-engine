"""Tests for domain-neutral entity production contracts."""

from __future__ import annotations

import random
from dataclasses import dataclass

from evo_engine.production import EntityProductionModel


@dataclass(frozen=True)
class Product:
    """Simple nonbiological produced entity used by contract tests."""

    state: str
    source_total: int
    context: str


class StringProduction:
    """Produce a simple entity from already-determined string state."""

    def produce(
        self,
        state: str,
        *,
        source_entities: tuple[int, ...],
        context: str,
        rng: random.Random,
    ) -> Product:
        del rng
        return Product(
            state=state,
            source_total=sum(source_entities),
            context=context,
        )


def _produce_with_generic_contract(
    model: EntityProductionModel[str, int, str, Product],
) -> Product:
    return model.produce(
        "already-determined",
        source_entities=(2, 3, 5),
        context="nonbiological",
        rng=random.Random(1),
    )


def test_entity_production_is_structurally_typed_and_domain_neutral() -> None:
    """Test the generic contract produces entities without propagation semantics."""
    result = _produce_with_generic_contract(StringProduction())

    assert result == Product(
        state="already-determined",
        source_total=10,
        context="nonbiological",
    )


def test_entity_production_accepts_zero_sources() -> None:
    """Test production itself places no source-count restriction."""
    result = StringProduction().produce(
        "seed",
        source_entities=(),
        context="abiotic",
        rng=random.Random(2),
    )

    assert result.source_total == 0
