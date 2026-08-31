"""Tests for biological genetics adapters to general contracts."""

from __future__ import annotations

import random

from evo_engine.genetics import (
    ChoiceAlleleDomain,
    ClonalInheritance,
    GeneticArchitecture,
    Genome,
    Locus,
    NoMutation,
    UniformChoiceMutation,
)


def test_locus_exposes_generic_linkage_coordinates() -> None:
    """Test biological chromosome coordinates map to general linkage semantics."""
    locus = Locus(
        name="color",
        chromosome_name="chromosome_2",
        position=150,
        domain=ChoiceAlleleDomain(values=("brown", "blue")),
        mutation=NoMutation(),
    )

    assert locus.linkage_group == "chromosome_2"
    assert locus.linkage_position == 150


def test_categorical_mutation_supports_noninteger_heritable_values() -> None:
    """Test categorical state can mutate without integer encoding."""
    mutation = UniformChoiceMutation(
        probability_ppm=1_000_000,
        choices=("brown", "green", "blue"),
    )

    result = mutation.mutate(
        "brown",
        rng=random.Random(1),
    )

    assert result in {"green", "blue"}


def test_mutation_policies_expose_general_variation_operation() -> None:
    """Test biological mutation implements general variation semantics."""
    mutation = UniformChoiceMutation(
        probability_ppm=1_000_000,
        choices=("a", "b"),
    )

    assert mutation.vary("a", rng=random.Random(1)) == "b"


def test_clonal_inheritance_adapts_to_general_propagation() -> None:
    """Test biological inheritance implements domain-neutral propagation."""
    architecture = GeneticArchitecture(loci=(), traits=())
    genome = Genome(chromosomes=())
    inheritance = ClonalInheritance()

    result = inheritance.propagate(
        (genome,),
        recipient=object(),
        context=architecture,
        rng=random.Random(1),
    )

    assert result == genome
    assert inheritance.parent_count == 1
