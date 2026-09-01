"""Tests for domain-neutral entity access contracts."""

from __future__ import annotations

from dataclasses import dataclass

from evo_engine.access import EntityAccessModel


@dataclass(frozen=True, slots=True)
class Product:
    """Represent a nonbiological entity used to test generic access."""

    sku: str


class InventoryAccess:
    """Read products from a nonbiological inventory mapping."""

    def get(self, reference: str, *, state: dict[str, Product]) -> Product:
        return state[reference]

    def entities(self, *, state: dict[str, Product]) -> tuple[Product, ...]:
        return tuple(state.values())


def read_first(
    access: EntityAccessModel[str, dict[str, Product], Product],
    inventory: dict[str, Product],
) -> Product:
    """Exercise structural typing through the generic access protocol."""
    first = access.entities(state=inventory)[0]
    return access.get(first.sku, state=inventory)


def test_entity_access_supports_nonbiological_state_and_references() -> None:
    """Test access has no organism, world, or integer-ID assumptions."""
    product = Product(sku="A-17")
    inventory = {product.sku: product}

    assert read_first(InventoryAccess(), inventory) is product


def test_entity_access_snapshot_is_stable_after_state_change() -> None:
    """Test enumeration returns a stable snapshot rather than a live view."""
    first = Product(sku="first")
    second = Product(sku="second")
    inventory = {first.sku: first}
    access = InventoryAccess()

    snapshot = access.entities(state=inventory)
    inventory[second.sku] = second

    assert snapshot == (first,)
    assert access.entities(state=inventory) == (first, second)
