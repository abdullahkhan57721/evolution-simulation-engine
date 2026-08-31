"""Tests for domain-neutral state propagation contracts."""

from __future__ import annotations

import random
from typing import assert_type

import attrs
import pytest

from evo_engine.propagation import PropagationModel, TransmissibleStateCarrier


@attrs.frozen(slots=True)
class _Recipient:
    offset: int


@attrs.frozen(slots=True)
class _IntegerCarrier:
    value: int

    @property
    def transmissible_state(self) -> int:
        return self.value


@attrs.frozen(slots=True)
class _SumPropagation:
    def propagate(
        self,
        source_states: tuple[int, ...],
        *,
        recipient: _Recipient,
        context: int,
        rng: random.Random,
    ) -> int:
        del rng
        return sum(source_states) + recipient.offset + context


def _propagate(
    model: PropagationModel[int, _Recipient, int],
    source_states: tuple[int, ...],
) -> int:
    return model.propagate(
        source_states,
        recipient=_Recipient(offset=5),
        context=7,
        rng=random.Random(1),
    )


@pytest.mark.parametrize(
    ("source_states", "expected"),
    [
        ((), 12),
        ((3,), 15),
        ((1, 2, 3), 18),
        ((1, 2, 3, 4, 5), 27),
    ],
)
def test_propagation_contract_imposes_no_source_count(
    source_states: tuple[int, ...],
    expected: int,
) -> None:
    """Test generic propagation supports zero, one, or many source states."""
    result = _propagate(_SumPropagation(), source_states)

    assert_type(result, int)
    assert result == expected


def test_propagation_receives_recipient_separately_from_sources() -> None:
    """Test recipient state can influence propagation without being a source."""
    model = _SumPropagation()

    first = model.propagate(
        (10,),
        recipient=_Recipient(offset=1),
        context=0,
        rng=random.Random(1),
    )
    second = model.propagate(
        (10,),
        recipient=_Recipient(offset=4),
        context=0,
        rng=random.Random(1),
    )

    assert first == 11
    assert second == 14


def test_transmissible_state_carrier_is_structural() -> None:
    """Test arbitrary participants can expose state through the generic contract."""
    carrier: TransmissibleStateCarrier[int] = _IntegerCarrier(value=9)

    assert_type(carrier.transmissible_state, int)
    assert carrier.transmissible_state == 9
