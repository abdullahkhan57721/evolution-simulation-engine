from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCIENTIFIC_WORKFLOWS = (
    "b3-confirmation.yml",
    "e3-scientific-validation.yml",
    "e4-scientific-validation.yml",
    "e5-scientific-validation.yml",
    "e6-scientific-validation.yml",
    "e7-scientific-validation.yml",
)


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_safe_fix_scope_matches_default_lint_scope() -> None:
    fix_script = _read("scripts/fix")
    lint_script = _read("scripts/lint")

    assert "set -- ." in fix_script
    assert "TARGETS=(.)" in lint_script
    assert "--unsafe-fixes" not in fix_script


def test_fast_checkpoint_keeps_final_checks_out_of_inner_loop() -> None:
    check_all = _read("scripts/check_all")

    assert "--fast" in check_all
    assert "fast_mode=1" in check_all
    assert "if [[ $fast_mode -eq 0 ]]; then" in check_all
    assert '"$SCRIPT_DIR/coverage"' in check_all
    assert '"$SCRIPT_DIR/docs"' in check_all


def test_quality_workflow_uses_one_draft_fast_job_and_full_non_draft_gate() -> None:
    quality = _read(".github/workflows/quality.yml")

    assert "name: Fast checkpoint" in quality
    assert "./scripts/check_all --fast --no-pause" in quality
    assert "github.event.pull_request.draft == true" in quality
    assert "github.event.pull_request.draft == false" in quality
    assert "ready_for_review" in quality
    assert "name: Ruff, Pyright, Architecture, Complexity, Tests, Docs" in quality
    assert "./scripts/coverage" in quality
    assert "Reference + kernel + world-presentation performance profiles" in quality


def test_expensive_smokes_are_deferred_until_non_draft_validation() -> None:
    release_smoke = _read(".github/workflows/release-smoke.yml")
    cinematic_smoke = _read(".github/workflows/cinematic-smoke.yml")

    for workflow in (release_smoke, cinematic_smoke):
        assert "ready_for_review" in workflow
        assert "github.event.pull_request.draft == false" in workflow


def test_frozen_scientific_workflows_follow_science_affecting_paths() -> None:
    for workflow_name in SCIENTIFIC_WORKFLOWS:
        workflow = _read(f".github/workflows/{workflow_name}")

        assert '"src/evo_engine/**"' in workflow
        assert "!src/evo_engine/ui/**" in workflow
        assert "!src/evo_engine/workbench/**" in workflow
        assert "!src/evo_engine/presentation/**" in workflow
        assert "!src/evo_engine/cinematic/**" in workflow
        assert "ready_for_review" in workflow
        assert "github.event.pull_request.draft == false" in workflow
        assert "docs/development/current_state.md" not in workflow
        assert "docs/development/roadmap.md" not in workflow
        assert '"mkdocs.yml"' not in workflow
