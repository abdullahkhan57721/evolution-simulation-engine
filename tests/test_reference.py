"""Tests for domain-neutral entity reference contracts."""

from __future__ import annotations

from evo_engine.reference import EntityReferenceModel


class CatalogReference:
    """Derive string references from an arbitrary nonbiological catalog."""

    def reference(
        self,
        entity: str,
        *,
        state: dict[str, str],
    ) -> str:
        for reference, stored_entity in state.items():
            if stored_entity == entity:
                return reference
        raise KeyError(entity)


def derive_reference(
    model: EntityReferenceModel[str, dict[str, str], str],
    entity: str,
    *,
    state: dict[str, str],
) -> str:
    """Exercise structural typing through the generic reference contract."""
    return model.reference(entity, state=state)


def test_entity_reference_model_supports_nonbiological_references() -> None:
    """Test references may use arbitrary entity, state, and reference types."""
    state = {"primary": "alpha", "secondary": "beta"}

    assert derive_reference(
        CatalogReference(),
        "beta",
        state=state,
    ) == "secondary"


def test_entity_reference_model_is_read_only() -> None:
    """Test deriving a reference does not require state mutation."""
    state = {"primary": "alpha"}
    before = state.copy()

    CatalogReference().reference("alpha", state=state)

    assert state == before
