from __future__ import annotations

from pathlib import Path

_QML = Path("src/evo_engine/desktop/qml")
_CONTROLLERS = Path("src/evo_engine/desktop/controllers")


def _text(name: str) -> str:
    return (_QML / name).read_text(encoding="utf-8")


def test_q2_shell_routes_scientific_authoring_through_thin_controllers() -> None:
    main = _text("Main.qml")
    assert main.count("applicationController.simulationController") == 1
    assert main.count("applicationController.evidenceController") == 1
    assert main.count("applicationController.experimentController") == 1
    assert "SimulationAuthoringView" in main
    assert "EvidenceAuthoringView" in main
    assert "ExperimentAuthoringView" in main


def test_q2_reference_surface_exposes_supported_disclosure_without_extension_controls() -> (
    None
):
    simulation = _text("SimulationAuthoringView.qml")
    assert "Reference Ecology · Guided" in simulation
    assert "Advanced supported choices" in simulation
    assert "GAUSSIAN STANDARD DEVIATION" in simulation
    assert "PATCH 1 CENTER X" in simulation
    assert "MUTATION PROBABILITY (PPM)" in simulation
    assert "RECOMBINATION PROBABILITY (PPM)" in simulation
    assert "Expert" not in simulation
    assert "Extension" not in simulation
    assert "arbitrary-resource-placement-policy" not in simulation
    assert "arbitrary-reference-traits" not in simulation


def test_q2_evidence_and_experiment_surfaces_remain_concrete() -> None:
    evidence = _text("EvidenceAuthoringView.qml")
    experiment = _text("ExperimentAuthoringView.qml")
    assert "evidence.optionModel" in evidence
    assert "saveEvidenceChildRevision" in evidence
    assert "experiment.factorLevelModel" in experiment
    assert "experiment.runModel" in experiment
    assert "Maximum-speed sweep" in experiment
    assert "Environment-selection comparison" in experiment
    assert "B3 flagship compiled design" in experiment
    assert "generic experiment editor" in experiment
    assert "schema" not in experiment.lower()
    assert "dsl" not in experiment.lower()


def test_q2_qml_does_not_own_scientific_manifest_or_revision_mutation() -> None:
    joined = "\n".join(
        _text(name)
        for name in (
            "SimulationAuthoringView.qml",
            "EvidenceAuthoringView.qml",
            "ExperimentAuthoringView.qml",
        )
    )
    assert "manifest." not in joined
    assert "revision." not in joined
    assert "evo_engine." not in joined


def test_q2_native_controllers_do_not_depend_on_streamlit_ui() -> None:
    joined = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(_CONTROLLERS.glob("*.py"))
    )
    assert "evo_engine.ui" not in joined
    assert "evo_engine.workbench.simulation_authoring" in joined
    assert "evo_engine.workbench.evidence_authoring" in joined
    assert "evo_engine.workbench.experiment_authoring" in joined
