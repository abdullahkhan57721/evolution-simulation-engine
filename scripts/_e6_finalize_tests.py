"""Temporarily finalize E6 test formatting and guard coverage."""

from __future__ import annotations

from pathlib import Path


TEST_PATH = Path("tests/experiments/test_e6_invasion_contracts.py")


def main() -> None:
    text = TEST_PATH.read_text(encoding="utf-8")
    text = text.replace(
        "def test_lineage_composition_validation_guards_complete_counts_and_frequencies() -> None:\n",
        "def test_lineage_composition_validation_guards_complete_counts_and_frequencies() -> (\n"
        "    None\n"
        "):\n",
        1,
    )
    text = text.replace(
        'match="same exact burn-in checkpoint"',
        'match="share one exact burn-in checkpoint"',
        1,
    )

    marker = "def test_additional_e6_guard_branches("
    if marker not in text:
        text += '''\n\ndef test_additional_e6_guard_branches(\n    pair: e6.E6InvasionPairOutcome,\n) -> None:\n    outcome = pair.neutral\n\n    wrong_types = (\n        ("provenance", "provenance"),\n        ("burn_in_checkpoint", "burn_in_checkpoint"),\n        ("intervention", "intervention"),\n    )\n    for field_name, match in wrong_types:\n        with pytest.raises(TypeError, match=match):\n            attrs.evolve(outcome, **{field_name: cast(Any, object())})\n\n    with pytest.raises(TypeError, match="rare_expansion"):\n        attrs.evolve(outcome, rare_expansion=cast(Any, object()))\n\n    with pytest.raises(TypeError, match="mutant"):\n        e6.E6InvasionPairOutcome(\n            neutral=pair.neutral,\n            mutant=cast(Any, object()),\n        )\n\n    with pytest.raises(ValueError, match="absent from pedigree"):\n        e6._required_pedigree_record({}, 12345)\n    with pytest.raises(ValueError, match="absent from pedigree"):\n        e6._required_lineage({}, 12345)\n\n    with pytest.raises(ValueError, match="every post-introduction committed state"):\n        e6._validated_trait_observations(())\n\n    with pytest.raises(TypeError, match="SimulationState"):\n        e6._world_state(cast(Any, object()))\n'''

    TEST_PATH.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
