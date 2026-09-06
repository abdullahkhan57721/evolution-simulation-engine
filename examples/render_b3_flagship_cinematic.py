"""Reproduce the confirmed B3 flagship cinematic from committed evidence."""

from __future__ import annotations

import argparse
import json
from importlib.metadata import version
from pathlib import Path

from evo_engine.cinematic.b3_api import render_b3_flagship_cinematic
from evo_engine.cinematic.b3_director import (
    B3_REPRESENTATIVE_SEED,
    prepare_b3_flagship_director,
)
from evo_engine.cinematic.b3_manifest import build_b3_flagship_render_manifest
from evo_engine.experiments.b3_flagship import (
    B3MatchedPairSummary,
    B3RunEvidence,
    B3RunSummary,
    run_b3_flagship,
    run_b3_matched_pair,
    summarize_b3_run,
)
from evo_engine.presets.reference_ecology.b3_flagship import (
    B3_CONFIRMATION_SEEDS,
    build_b3_flagship_specification,
)


def main() -> None:
    """Run the frozen B3 evidence path, prepare the director, and render it."""
    arguments = _parse_arguments()
    control, treatment = _representative_evidence()
    if arguments.excerpt:
        confirmation: tuple[B3MatchedPairSummary, ...] = ()
        broad: tuple[B3RunSummary, ...] = ()
    else:
        confirmation = _confirmation_summaries(control, treatment)
        broad = _broad_patch_summaries()

    plan = prepare_b3_flagship_director(
        control_evidence=control,
        treatment_evidence=treatment,
        confirmation_pairs=confirmation,
        broad_patch_summaries=broad,
    )
    output_path = render_b3_flagship_cinematic(
        plan,
        arguments.output,
        quality=arguments.quality,
    )
    manifest = build_b3_flagship_render_manifest(
        plan,
        renderer_version=version("manim"),
        quality=arguments.quality,
    )
    manifest_path = output_path.with_suffix(".manifest.json")
    manifest_path.write_text(
        json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    mode = "reduced B3 director excerpt" if arguments.excerpt else "full B3 flagship"
    print(f"Rendered {mode}: {output_path}")
    print(f"Recorded cinematic manifest: {manifest_path}")


def _representative_evidence() -> tuple[B3RunEvidence, B3RunEvidence]:
    control = run_b3_flagship(
        build_b3_flagship_specification(
            seed=B3_REPRESENTATIVE_SEED,
            environment="uniform",
        )
    )
    treatment = run_b3_flagship(
        build_b3_flagship_specification(
            seed=B3_REPRESENTATIVE_SEED,
            environment="compact_patch",
        )
    )
    return control, treatment


def _confirmation_summaries(
    representative_control: B3RunEvidence,
    representative_treatment: B3RunEvidence,
) -> tuple[B3MatchedPairSummary, ...]:
    representative = B3MatchedPairSummary(
        seed=B3_REPRESENTATIVE_SEED,
        founder_assignment="standard",
        control=summarize_b3_run(representative_control),
        treatment=summarize_b3_run(representative_treatment),
    )
    pairs: dict[int, B3MatchedPairSummary] = {B3_REPRESENTATIVE_SEED: representative}
    for seed in B3_CONFIRMATION_SEEDS:
        if seed == B3_REPRESENTATIVE_SEED:
            continue
        pairs[seed] = run_b3_matched_pair(seed=seed)
    return tuple(pairs[seed] for seed in B3_CONFIRMATION_SEEDS)


def _broad_patch_summaries() -> tuple[B3RunSummary, ...]:
    return tuple(
        summarize_b3_run(
            run_b3_flagship(
                build_b3_flagship_specification(
                    seed=seed,
                    environment="broad_patch",
                )
            )
        )
        for seed in B3_CONFIRMATION_SEEDS
    )


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Reproduce the confirmed B3 environment-dependent max-speed cinematic. "
            "The default runs the full independent confirmation and radius-2 "
            "sensitivity evidence; --excerpt keeps the same director path but renders "
            "only the representative evidence acts for routine smoke validation."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/b3-flagship-cinematic.mp4"),
        help="Destination .mp4 or .gif path.",
    )
    parser.add_argument(
        "--quality",
        choices=("low", "medium", "high"),
        default="medium",
        help="Manim render quality preset.",
    )
    parser.add_argument(
        "--excerpt",
        action="store_true",
        help=(
            "Render the reduced real B3 director excerpt without rerunning the full "
            "confirmation/sensitivity set."
        ),
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
