from pathlib import Path

application_path = Path("src/evo_engine/desktop/controllers/application.py")
application = application_path.read_text(encoding="utf-8")
start = application.index("    def _bind_pending_scientific_state_for_run(\n")
end = application.index("    @Slot(object, object, object)\n", start)
replacement = '''    def _bind_pending_scientific_state_for_run(
        self,
    ) -> tuple[ConcreteWorkbenchArtifact, str | None]:
        artifact = self._artifact
        if artifact is None:
            raise ValueError("No active Study is available for Run.")
        if isinstance(artifact, StudyRevision):
            return self._bind_pending_controlled_for_run(artifact)
        if isinstance(artifact, ReferenceStudyRevision):
            return self._bind_pending_reference_for_run(artifact)
        if isinstance(
            artifact,
            (MaxSpeedSweepDefinition, EnvironmentSelectionComparisonDefinition),
        ):
            return self._bind_pending_experiment_for_run(artifact)
        if isinstance(artifact, B3StudyRevision):
            return artifact, None
        raise TypeError("Unsupported Workbench artifact for Run binding.")

    def _bind_pending_controlled_for_run(
        self, artifact: StudyRevision
    ) -> tuple[StudyRevision, str | None]:
        intent = self._simulation.controlled_draft_intent() or artifact.intent
        plan = self._evidence.draft_plan()
        if not isinstance(plan, EvidencePlan):
            raise TypeError("Controlled Study requires EvidencePlan.")
        readiness = assess_readiness(intent, plan)
        if readiness.state != "ready":
            raise WorkbenchNotReadyError(readiness)
        if intent == artifact.intent and plan == artifact.evidence_plan:
            return artifact, None
        child = fork_study_revision(
            artifact,
            revision_id=_new_revision_id("controlled-run"),
            max_speed=cast(int, intent.max_speed),
            resource_geography=cast(str, intent.resource_geography),
            seed=cast(int, intent.seed),
            evidence_plan=plan,
        )
        self._activate_artifact(child, file_path=None, reset_section=False)
        return (
            child,
            "Pending Simulation/Evidence edits were bound atomically to immutable "
            f"revision {child.revision_id} before Run.",
        )

    def _bind_pending_reference_for_run(
        self, artifact: ReferenceStudyRevision
    ) -> tuple[ReferenceStudyRevision, str | None]:
        intent = normalize_reference_draft(
            self._reference.draft_intent() or artifact.intent
        )
        plan = self._evidence.draft_plan()
        if not isinstance(plan, ReferenceEvidencePlan):
            raise TypeError("Reference Study requires ReferenceEvidencePlan.")
        readiness = assess_reference_readiness(intent, plan)
        if readiness.state != "ready":
            raise WorkbenchNotReadyError(readiness)
        if intent == artifact.intent and plan == artifact.evidence_plan:
            return artifact, None
        child = fork_reference_study_revision(
            artifact,
            revision_id=_new_revision_id("reference-run"),
            intent=intent,
            evidence_plan=plan,
        )
        self._activate_artifact(child, file_path=None, reset_section=False)
        return (
            child,
            "Pending Simulation/Evidence edits were bound atomically to immutable "
            f"revision {child.revision_id} before Run.",
        )

    def _bind_pending_experiment_for_run(
        self,
        artifact: MaxSpeedSweepDefinition | EnvironmentSelectionComparisonDefinition,
    ) -> tuple[
        MaxSpeedSweepDefinition | EnvironmentSelectionComparisonDefinition,
        str | None,
    ]:
        candidate = self._experiment.definition_for_run()
        if candidate is None:
            raise ValueError("Experiment draft is invalid or unavailable.")
        if candidate == artifact:
            return artifact, None
        self._activate_artifact(candidate, file_path=None, reset_section=False)
        return (
            candidate,
            "Pending Experiment edits were bound to this exact immutable experiment "
            "definition before Run.",
        )

'''
application_path.write_text(application[:start] + replacement + application[end:], encoding="utf-8")

ui_test_path = Path("tests/ui/test_run_execution.py")
ui_test = ui_test_path.read_text(encoding="utf-8")
old = '    monkeypatch.setattr(workbench_execution, "run_environment_selection_comparison", fake_e4)\n'
new = '''    monkeypatch.setattr(
        workbench_execution, "run_environment_selection_comparison", fake_e4
    )
'''
if old not in ui_test:
    raise RuntimeError("Expected Ruff-format target was not found.")
ui_test_path.write_text(ui_test.replace(old, new), encoding="utf-8")
