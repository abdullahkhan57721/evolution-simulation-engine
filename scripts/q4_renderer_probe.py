#!/usr/bin/env python3
"""Capture repeatable offscreen Q4 renderer measurements and visual proof."""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, cast

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import qVersion
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickWindow

import evo_engine.desktop.controllers.presentation as presentation_module
from evo_engine.desktop.controllers import ApplicationController, PresentationController
from evo_engine.desktop.main import create_engine
from evo_engine.experiments.science import ScientificRunProvenance
from evo_engine.presentation.scientific import ContinuousTraitEncoding
from evo_engine.presentation.world import (
    CarcassPrimitive,
    MovementTrail,
    OrganismPrimitive,
    ResourcePrimitive,
    WorldPresentationFrame,
)
from evo_engine.workbench import (
    B3CuratedRunResult,
    ReferenceRunResult,
    WorkbenchRunProvenance,
)
from evo_engine.workbench.results import AnalysisAvailability


def _scientific_provenance() -> ScientificRunProvenance:
    return ScientificRunProvenance(
        experiment_id="q4-renderer-probe",
        scenario_id="q4-renderer-probe",
        treatment_id="q4-renderer-probe",
        treatment_specification_json="{}",
        seed=17,
        horizon_step_index=1,
        observation_every_n_steps=1,
        observation_include_step_zero=True,
        focal_variables=("population_size",),
        run_role="representative",
    )


def _workbench_provenance(revision: Any, *, run_id: str) -> WorkbenchRunProvenance:
    return WorkbenchRunProvenance(
        run_id=run_id,
        study_revision_id=revision.revision_id,
        manifest_digest=revision.manifest.digest,
        evidence_ids=revision.evidence_plan.requested,
        evidence_references=(),
        result_references=(),
    )


def _reference_result(revision: Any) -> ReferenceRunResult:
    return ReferenceRunResult(
        provenance=_workbench_provenance(revision, run_id="q4-probe-reference"),
        scientific_provenance=_scientific_provenance(),
        population_observations=(),
        applied_events=(),
        pedigree_records=(),
        genetic_observations=(),
        spatial_observations=(),
    )


def _b3_result(revision: Any) -> B3CuratedRunResult:
    return B3CuratedRunResult(
        provenance=_workbench_provenance(revision, run_id="q4-probe-b3"),
        scenario_origin=revision.scenario_origin,
        scenario_identity=revision.scenario_identity,
        confirmation=(),
        radius_sensitivity=(),
        counterbalanced=(),
    )


def _available() -> AnalysisAvailability:
    return AnalysisAvailability(
        analysis_id="q4.renderer.probe",
        source_contract="synthetic canonical WorldPresentationFrame probe",
        required_evidence_ids=(),
    )


def _frame(
    step: int,
    *,
    population_size: int,
    encoding: ContinuousTraitEncoding | None,
    offset: int = 0,
) -> WorldPresentationFrame:
    width = 48
    height = 32
    organisms = []
    trails = []
    for index in range(population_size):
        organism_id = index + 1
        x = (index * 7 + step + offset) % width
        y = (index * 11 + step * 2) % height
        trait_value = 1 + (index % 9)
        organisms.append(
            OrganismPrimitive(
                organism_id=organism_id,
                x=x,
                y=y,
                age=5 + step,
                energy=70 + (index % 25),
                body_mass=2 + (index % 3),
                mating_type="A" if index % 2 == 0 else "B",
                marker_size=12,
                focal_trait_value=trait_value if encoding is not None else None,
                focal_trait_normalized=(trait_value - 1) / 8
                if encoding is not None
                else None,
            )
        )
        if index < min(population_size, 128):
            trails.append(
                MovementTrail(
                    organism_id=organism_id,
                    points=tuple(
                        (
                            (x - trail_step) % width,
                            (y - trail_step) % height,
                        )
                        for trail_step in range(5, -1, -1)
                    ),
                )
            )
    resources = tuple(
        ResourcePrimitive(x=(index * 5) % width, y=(index * 9) % height, amount=5)
        for index in range(48)
    )
    carcasses = tuple(
        CarcassPrimitive(
            carcass_id=index + 1,
            x=(index * 13) % width,
            y=(index * 3) % height,
            resource_units=3,
        )
        for index in range(12)
    )
    return WorldPresentationFrame(
        committed_step_index=step,
        world_width=width,
        world_height=height,
        organisms=tuple(organisms),
        resources=resources,
        carcasses=carcasses,
        trails=tuple(trails),
        focal_encoding=encoding,
    )


def _measure(
    app: QGuiApplication,
    action: Callable[[], None],
    *,
    repetitions: int = 3,
) -> dict[str, float]:
    samples_ms: list[float] = []
    for _ in range(repetitions):
        started = time.perf_counter()
        action()
        app.processEvents()
        samples_ms.append((time.perf_counter() - started) * 1000)
    return {
        "min_ms": round(min(samples_ms), 3),
        "mean_ms": round(sum(samples_ms) / len(samples_ms), 3),
        "max_ms": round(max(samples_ms), 3),
    }


def _measure_with_setup(
    app: QGuiApplication,
    setup: Callable[[], None],
    action: Callable[[], None],
    *,
    repetitions: int = 3,
) -> dict[str, float]:
    samples_ms: list[float] = []
    for _ in range(repetitions):
        setup()
        app.processEvents()
        started = time.perf_counter()
        action()
        app.processEvents()
        samples_ms.append((time.perf_counter() - started) * 1000)
    return {
        "min_ms": round(min(samples_ms), 3),
        "mean_ms": round(sum(samples_ms) / len(samples_ms), 3),
        "max_ms": round(max(samples_ms), 3),
    }


def _save_window(window: QQuickWindow, path: Path) -> None:
    image = window.grabWindow()
    if image.isNull() or not image.save(str(path)):
        raise RuntimeError(f"Could not capture renderer proof at {path}.")


def _bind_reference(
    controller: ApplicationController,
    presentation: PresentationController,
    app: QGuiApplication,
    state: dict[str, int],
) -> None:
    assert controller.createStudy("reference-ecology")
    revision = controller._artifact
    assert revision is not None

    view = SimpleNamespace(
        spatial_availability=_available(),
        spatial_observations=(0, 1),
    )

    def inspect_reference(*_args: Any, **_kwargs: Any) -> Any:
        return view

    def available_steps(observations: Any) -> tuple[int, ...]:
        return tuple(observations)

    def build_reference(
        *_args: Any,
        step_index: int,
        selected_organism_id: int | None = None,
        **_kwargs: Any,
    ) -> Any:
        frame = _frame(
            step_index,
            population_size=state["population_size"],
            encoding=None,
        )
        if selected_organism_id is not None:
            selected = tuple(
                OrganismPrimitive(
                    organism_id=item.organism_id,
                    x=item.x,
                    y=item.y,
                    age=item.age,
                    energy=item.energy,
                    body_mass=item.body_mass,
                    mating_type=item.mating_type,
                    marker_size=item.marker_size,
                    selected=item.organism_id == selected_organism_id,
                    focal_trait_value=item.focal_trait_value,
                    focal_trait_normalized=item.focal_trait_normalized,
                )
                for item in frame.organisms
            )
            frame = WorldPresentationFrame(
                committed_step_index=frame.committed_step_index,
                world_width=frame.world_width,
                world_height=frame.world_height,
                organisms=selected,
                resources=frame.resources,
                carcasses=frame.carcasses,
                trails=frame.trails,
                selected_organism_id=selected_organism_id,
                focal_encoding=frame.focal_encoding,
            )
        return SimpleNamespace(frame=frame)

    presentation_module.inspect_reference_study_results = inspect_reference
    presentation_module.available_step_indices = available_steps
    presentation_module.build_reference_workbench_world_presentation = build_reference
    controller._result = _reference_result(revision)
    controller._presentation_owner = "q4-probe-reference-owner"
    controller.presentationChanged.emit()
    assert controller.selectSection("Presentation")
    app.processEvents()
    assert presentation.available and presentation.family == "reference"


def _bind_b3(
    controller: ApplicationController,
    presentation: PresentationController,
    app: QGuiApplication,
) -> None:
    assert controller.createStudy("b3-flagship")
    revision = controller._artifact
    assert revision is not None
    pair = SimpleNamespace(
        summary=SimpleNamespace(seed=17),
        control_evidence=SimpleNamespace(spatial_observations=(0, 1)),
        treatment_evidence=SimpleNamespace(spatial_observations=(0, 1)),
    )
    encoding = ContinuousTraitEncoding(
        trait_name="max_speed",
        label="Maximum speed",
        lower_bound=1,
        upper_bound=9,
    )

    def inspect_b3(*_args: Any, **_kwargs: Any) -> Any:
        return SimpleNamespace(confirmation=(pair,))

    def build_b3(
        *_args: Any,
        arm: str,
        step_index: int,
        **_kwargs: Any,
    ) -> Any:
        return SimpleNamespace(
            frame=_frame(
                step_index,
                population_size=128,
                encoding=encoding,
                offset=0 if arm == "control" else 5,
            )
        )

    presentation_module.inspect_b3_results = inspect_b3
    presentation_module.build_b3_workbench_world_presentation = build_b3
    controller._result = _b3_result(revision)
    controller._presentation_owner = "q4-probe-b3-owner"
    controller.presentationChanged.emit()
    assert controller.selectSection("Presentation")
    app.processEvents()
    assert presentation.available and presentation.family == "b3"


def run_probe(output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    app = cast(QGuiApplication, QGuiApplication.instance() or QGuiApplication([]))
    engine, controller = create_engine()
    presentation = engine.rootContext().contextProperty("presentationController")
    if not isinstance(presentation, PresentationController):
        raise RuntimeError("Q4 PresentationController was not exposed to QML.")
    roots = engine.rootObjects()
    if not roots or not isinstance(roots[0], QQuickWindow):
        raise RuntimeError("Native QML root is not a QQuickWindow.")
    window = cast(QQuickWindow, roots[0])
    window.resize(1440, 900)
    app.processEvents()

    state = {"population_size": 64}
    _bind_reference(controller, presentation, app, state)
    owner_counter = 0

    def refresh_reference() -> None:
        nonlocal owner_counter
        owner_counter += 1
        controller._presentation_owner = f"q4-probe-reference-{owner_counter}"
        controller.presentationChanged.emit()

    measurements: dict[str, Any] = {
        "qt_version": qVersion(),
        "platform": os.environ.get("QT_QPA_PLATFORM", ""),
        "interpretation": (
            "Wall-clock offscreen projection + Qt Quick event-processing measurements; "
            "scientific values are canonical WorldPresentationFrame values."
        ),
    }

    state["population_size"] = 64
    measurements["reference_64_organisms"] = _measure(app, refresh_reference)
    state["population_size"] = 256
    measurements["reference_256_organisms"] = _measure(app, refresh_reference)

    measurements["labels_toggle_256"] = _measure(app, presentation.toggleLabels)
    measurements["trails_toggle_256"] = _measure(app, presentation.toggleTrails)

    measurements["adjacent_playback_step_256"] = _measure_with_setup(
        app,
        lambda: presentation.seekStepPosition(0),
        presentation.nextStep,
    )

    resize_sizes = [(1200, 760), (1600, 980), (1440, 900)]
    resize_index = 0

    def resize_window() -> None:
        nonlocal resize_index
        width, height = resize_sizes[resize_index % len(resize_sizes)]
        resize_index += 1
        window.resize(width, height)

    measurements["resize_reference_256"] = _measure(app, resize_window)
    window.resize(1440, 900)
    if not presentation.labelsVisible:
        presentation.toggleLabels()
    if not presentation.trailsVisible:
        presentation.toggleTrails()
    app.processEvents()
    _save_window(window, output_dir / "reference-256.png")

    b3_started = time.perf_counter()
    _bind_b3(controller, presentation, app)
    measurements["b3_pair_128_per_arm"] = {
        "single_bind_ms": round((time.perf_counter() - b3_started) * 1000, 3)
    }
    _save_window(window, output_dir / "b3-pair-128-per-arm.png")

    (output_dir / "measurements.json").write_text(
        json.dumps(measurements, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return measurements


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("q4-renderer-proof"),
        help="Directory for screenshots and measurements.json.",
    )
    args = parser.parse_args()
    measurements = run_probe(args.output_dir)
    print(json.dumps(measurements, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
