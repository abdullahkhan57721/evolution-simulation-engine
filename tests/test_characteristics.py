"""Tests for domain-neutral characteristic access and requirements."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from evo_engine.characteristics import (
    CharacteristicRequirementProvider,
    CharacteristicSource,
    collect_required_characteristics,
    validate_required_characteristics,
)


@dataclass(frozen=True)
class Record:
    """Simple entity carrying arbitrary named values."""

    values: dict[str, int]


@dataclass(frozen=True)
class LookupContext:
    """Context used by the test characteristic source."""

    offset: int = 0


class MappingCharacteristicSource:
    """Read named values from a record and apply a context offset."""

    def value_for(
        self,
        entity: Record,
        characteristic_name: str,
        *,
        context: LookupContext,
    ) -> int:
        return entity.values[characteristic_name] + context.offset


@dataclass(frozen=True)
class RequirementSet:
    """Declare arbitrary characteristic requirements."""

    required_characteristics: frozenset[str]


def test_characteristic_source_protocol_supports_nonbiological_entities() -> None:
    """Test characteristic lookup is independent of modeled-domain representation."""
    source: CharacteristicSource[Record, LookupContext, int] = (
        MappingCharacteristicSource()
    )

    assert (
        source.value_for(
            Record(values={"latency": 5}),
            "latency",
            context=LookupContext(offset=2),
        )
        == 7
    )


def test_requirement_provider_protocol_is_structural() -> None:
    """Test requirement providers need only expose the declared property."""
    provider = RequirementSet(required_characteristics=frozenset({"latency"}))

    assert isinstance(provider, CharacteristicRequirementProvider)


def test_collect_required_characteristics_unions_structural_providers() -> None:
    """Test requirement collection ignores unrelated components and deduplicates."""
    collected = collect_required_characteristics(
        RequirementSet(required_characteristics=frozenset({"latency", "throughput"})),
        object(),
        RequirementSet(required_characteristics=frozenset({"throughput", "cost"})),
    )

    assert collected == frozenset({"latency", "throughput", "cost"})


@pytest.mark.parametrize(
    "value",
    [
        {"latency"},
        ("latency",),
        ["latency"],
    ],
)
def test_validate_required_characteristics_requires_frozenset(value: object) -> None:
    """Test requirement collections use an immutable public contract."""
    with pytest.raises(TypeError, match="frozenset"):
        validate_required_characteristics(value)


@pytest.mark.parametrize(
    "value",
    [
        frozenset({""}),
        frozenset({"   "}),
    ],
)
def test_validate_required_characteristics_rejects_blank_names(
    value: frozenset[str],
) -> None:
    """Test characteristic names are nonblank."""
    with pytest.raises(ValueError, match="blank"):
        validate_required_characteristics(value)
