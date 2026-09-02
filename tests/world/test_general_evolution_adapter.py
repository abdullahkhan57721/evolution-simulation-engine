"""Tests for the organism adapter to general propagation contracts."""

from __future__ import annotations

from typing import assert_type

from evo_engine.genetics import Genome
from evo_engine.propagation import TransmissibleStateCarrier
from tests.helpers import make_organism


def test_organism_exposes_genome_as_transmissible_state() -> None:
    """Test biology exposes one generic carrier adapter without old aliases."""
    organism = make_organism()
    carrier: TransmissibleStateCarrier[Genome] = organism

    assert_type(carrier.transmissible_state, Genome)
    assert carrier.transmissible_state is organism.genome
    assert not hasattr(organism, "heritable_state")
