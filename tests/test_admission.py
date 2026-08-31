"""Tests for domain-neutral entity admission contracts."""

from __future__ import annotations

from evo_engine.admission import EntityAdmissionModel


class StringAdmission:
    """Admit strings into a simple nonbiological registry."""

    def admit(
        self,
        entity: str,
        *,
        state: list[str],
    ) -> None:
        state.append(entity)


def _admit_with_generic_contract(
    model: EntityAdmissionModel[str, list[str]],
    state: list[str],
) -> None:
    model.admit(
        "produced-entity",
        state=state,
    )


def test_entity_admission_is_structurally_typed_and_domain_neutral() -> None:
    """Test generic admission adds arbitrary entities to arbitrary state."""
    state: list[str] = []

    _admit_with_generic_contract(
        StringAdmission(),
        state,
    )

    assert state == ["produced-entity"]


def test_entity_admission_has_no_rng_or_production_inputs() -> None:
    """Test mechanical admission needs only the produced entity and target state."""
    state: list[str] = ["existing"]

    StringAdmission().admit(
        "new",
        state=state,
    )

    assert state == ["existing", "new"]
