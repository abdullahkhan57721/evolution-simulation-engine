"""Focused tests for completed-result workspace presentation helpers."""

from evo_engine.observation import CategoryCounts, IntegerSummary, PopulationObservation
from evo_engine.presets import ReferenceEcologyConfig
from evo_engine.ui.models import DashboardRun
from evo_engine.ui.workspace import _final_mean_energy


def test_final_mean_energy_handles_extinct_population() -> None:
    """Test an authoritative empty final population renders without formatting errors."""
    empty_summary = IntegerSummary(count=0, total=0)
    observation = PopulationObservation(
        step_index=1,
        population_size=0,
        carcass_count=0,
        total_resources=10,
        age=empty_summary,
        energy=empty_summary,
        body_mass=empty_summary,
        mating_type_counts=CategoryCounts(),
    )
    run = DashboardRun(
        config=ReferenceEcologyConfig(),
        completed_steps=1,
        population_history=(observation,),
        genetic_history=(),
        spatial_history=(),
        telemetry_steps=(),
        life_histories=(),
    )

    assert _final_mean_energy(run) == "—"
