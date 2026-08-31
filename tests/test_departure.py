"""Tests for domain-neutral entity departure contracts."""

from __future__ import annotations

from dataclasses import dataclass

from evo_engine.departure import EntityDepartureModel


@dataclass
class Registry:
    """Simple nonbiological mutable state used by departure contract tests."""

    entities: dict[str, int]


class RegistryDeparture:
    """Remove integer entities from a nonbiological registry."""

    def depart(
        self,
        reference: str,
        *,
        state: Registry,
    ) -> int:
        return state.entities.pop(reference)


def _depart_with_generic_contract(
    model: EntityDepartureModel[str, Registry, int],
    state: Registry,
) -> int:
    return model.depart("worker-2", state=state)


def test_entity_departure_is_structurally_typed_and_domain_neutral() -> None:
    """Test generic departure removes and returns a nonbiological entity."""
    state = Registry(entities={"worker-1": 10, "worker-2": 20})

    departed = _depart_with_generic_contract(RegistryDeparture(), state)

    assert departed == 20
    assert state.entities == {"worker-1": 10}


def test_entity_departure_contains_no_mortality_semantics() -> None:
    """Test ordinary nonbiological removal needs no death or cause concept."""
    state = Registry(entities={"cached-result": 7})

    departed = RegistryDeparture().depart("cached-result", state=state)

    assert departed == 7
    assert state.entities == {}
