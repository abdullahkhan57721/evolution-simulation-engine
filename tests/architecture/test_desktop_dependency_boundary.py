from __future__ import annotations

from pathlib import Path


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_lower_packages_do_not_depend_on_native_desktop_or_qt() -> None:
    source = _root() / "src" / "evo_engine"
    violations: list[str] = []
    for path in source.rglob("*.py"):
        if "desktop" in path.relative_to(source).parts:
            continue
        text = path.read_text(encoding="utf-8")
        if "evo_engine.desktop" in text or "PySide6" in text:
            violations.append(str(path.relative_to(_root())))
    assert violations == []


def test_native_desktop_does_not_depend_on_streamlit_ui() -> None:
    desktop = _root() / "src" / "evo_engine" / "desktop"
    violations: list[str] = []
    for path in desktop.rglob("*.py"):
        if "evo_engine.ui" in path.read_text(encoding="utf-8"):
            violations.append(str(path.relative_to(_root())))
    assert violations == []


def test_qt_is_not_a_core_project_dependency() -> None:
    pyproject = (_root() / "pyproject.toml").read_text(encoding="utf-8")
    project_dependencies = pyproject.split("[project.urls]", maxsplit=1)[0]
    assert "PySide6" not in project_dependencies
    assert "PySide6==6.11.2" in (_root() / "requirements-desktop.txt").read_text(
        encoding="utf-8"
    )


def test_qml_contains_only_curated_application_and_authoring_calls() -> None:
    qml_root = _root() / "src" / "evo_engine" / "desktop" / "qml"
    qml = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(qml_root.glob("*.qml"))
    )
    main = (qml_root / "Main.qml").read_text(encoding="utf-8")
    simulation = (qml_root / "SimulationAuthoringView.qml").read_text(encoding="utf-8")

    assert "evo_engine." not in qml
    assert "manifestDigest =" not in qml
    assert "revisionId =" not in qml
    assert "draftMaxSpeed = value" not in main
    assert "draftMaxSpeed = value" in simulation
