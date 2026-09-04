"""Run a focused B3 single-oasis experiment on current main.

Temporary analysis instrumentation only. It tests whether one shared distant resource
patch preserves the B1×B2 mobility mechanism while allowing ordinary reproduction.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import attrs

from evo_engine.ecology import PatchyResourcePlacement, ResourcePatch, UniformResourcePlacement
from evo_engine.engine import Simulation
from evo_engine.genetics import GENETIC_ARCHITECTURE, MAX_SPEED
from evo_engine.presets.reference_ecology.config import ReferenceEcologyConfig
from evo_engine.presets.reference_ecology.genetics import build_balanced_reference_trait_world
from evo_engine.presets.reference_ecology.observable import build_reference_ecology
from evo_engine.world import WorldState

LOW_SPEED = 1
HIGH_SPEED = 4
SEEDS = (11, 23, 37, 41, 59, 73, 89, 101)
MAX_STEPS = 50


class IndividualStateRecorder:
    """Record selected committed per-organism values for analysis."""

    def __init__(self) -> None:
        self.speed_by_id: dict[int, int] = {}
        self.energy_by_step: dict[int, dict[int, int]] = {}
        self.position_by_step: dict[int, dict[int, tuple[int, int]]] = {}

    def should_observe(self, world_state: WorldState, *, step_index: int) -> bool:
        del world_state, step_index
        return True

    def observe(self, world_state: WorldState, *, step_index: int) -> None:
        energies: dict[int, int] = {}
        positions: dict[int, tuple[int, int]] = {}
        for organism_id, organism in world_state.organisms.items():
            self.speed_by_id[organism_id] = organism.genetic_phenotype.int_value(MAX_SPEED)
            energies[organism_id] = organism.energy
            positions[organism_id] = (organism.x, organism.y)
        self.energy_by_step[step_index] = energies
        self.position_by_step[step_index] = positions


def _oasis(*, y: int, radius: int) -> PatchyResourcePlacement:
    return PatchyResourcePlacement(patches=(ResourcePatch(center_x=6, center_y=y, radius=radius),))


def _environment_specs() -> dict[str, tuple[int, object]]:
    return {
        "uniform_d16": (16, UniformResourcePlacement()),
        "oasis_y6_r2_d16": (16, _oasis(y=6, radius=2)),
        "oasis_y5_r3_d16": (16, _oasis(y=5, radius=3)),
        "uniform_d32": (32, UniformResourcePlacement()),
        "oasis_y6_r2_d32": (32, _oasis(y=6, radius=2)),
        "oasis_y5_r3_d32": (32, _oasis(y=5, radius=3)),
    }


def _config(*, seed: int, deposits: int, placement: object) -> ReferenceEcologyConfig:
    baseline = ReferenceEcologyConfig()
    return attrs.evolve(
        baseline,
        initial_population=20,
        initial_energy=30,
        max_steps=MAX_STEPS,
        seed=seed,
        mutation_probability_ppm=0,
        resource_generation_amount=6,
        resource_deposits_per_step=deposits,
        resource_placement_model=placement,
        mating_radius=3,
        traits=attrs.evolve(baseline.traits, attack_strength=0, defense=1),
    )


def _dist(values: list[int]) -> dict[str, float | int | None]:
    return {"count": len(values), "mean": sum(values) / len(values) if values else None, "total": sum(values)}


def _run_one(*, label: str, seed: int, deposits: int, placement: object) -> dict[str, Any]:
    recorder = IndividualStateRecorder()
    config = _config(seed=seed, deposits=deposits, placement=placement)
    ecology = build_reference_ecology(config, additional_observers=(recorder,))
    architecture = ecology.simulation.context.require(GENETIC_ARCHITECTURE)
    world = build_balanced_reference_trait_world(
        architecture, trait_name=MAX_SPEED, variant_values=(LOW_SPEED, HIGH_SPEED), config=config
    )
    simulation = Simulation(initial_domain_state=world, seed=seed, context=ecology.simulation.context)
    ecology.engine.run(simulation)

    genetic_history = []
    for observation in ecology.genetic_recorder.observations:
        locus = observation.locus(MAX_SPEED)
        genetic_history.append({
            "step": observation.step_index,
            "population": observation.population_size,
            "high_allele_frequency": locus.allele_frequency(HIGH_SPEED),
            "genotypes": [{"alleles": list(item.allele_values), "count": item.count, "frequency": item.frequency} for item in locus.genotypes],
        })

    population_history = []
    for observation in ecology.recorder.observations:
        speed_summary = next(item for item in observation.traits if item.trait_name == MAX_SPEED)
        population_history.append({
            "step": observation.step_index,
            "population": observation.population_size,
            "resources": observation.total_resources,
            "mean_energy": observation.energy.mean,
            "mean_speed": speed_summary.summary.mean,
            "speed_counts": [list(item) for item in speed_summary.value_counts],
        })

    consumption = {LOW_SPEED: 0, HIGH_SPEED: 0}
    targeted_moves = {LOW_SPEED: 0, HIGH_SPEED: 0}
    metabolism_energy = {LOW_SPEED: 0, HIGH_SPEED: 0}
    movement_energy = {LOW_SPEED: 0, HIGH_SPEED: 0}
    movement_examples: dict[int, dict[str, Any] | None] = {LOW_SPEED: None, HIGH_SPEED: None}
    reproduction_events: list[dict[str, Any]] = []
    consumption_by_step_id: dict[tuple[int, int], int] = {}

    for applied in ecology.event_recorder.events:
        event = applied.event
        oid = getattr(event, "organism_id", None)
        if applied.process_name == "ResourceConsumption" and type(oid) is int:
            amount = getattr(event, "amount", 0)
            if type(amount) is int:
                consumption_by_step_id[(applied.event_step_index + 1, oid)] = amount

    for applied in ecology.event_recorder.events:
        event = applied.event
        oid = getattr(event, "organism_id", None)
        if type(oid) is int:
            speed = recorder.speed_by_id.get(oid)
            if speed in (LOW_SPEED, HIGH_SPEED):
                if applied.process_name == "ResourceConsumption":
                    amount = getattr(event, "amount", 0)
                    if type(amount) is int:
                        consumption[speed] += amount
                elif applied.process_name == "Metabolism":
                    cost = getattr(event, "energy_cost", 0)
                    if type(cost) is int:
                        metabolism_energy[speed] += cost
                elif applied.process_name == "Movement":
                    cost = getattr(event, "energy_cost", 0)
                    if type(cost) is int:
                        movement_energy[speed] += cost
                    tx = getattr(event, "target_x", None)
                    ty = getattr(event, "target_y", None)
                    if tx is not None:
                        targeted_moves[speed] += 1
                        if movement_examples[speed] is None:
                            dx = getattr(event, "dx", 0)
                            dy = getattr(event, "dy", 0)
                            nx = getattr(event, "new_x", None)
                            ny = getattr(event, "new_y", None)
                            completed = applied.event_step_index + 1
                            movement_examples[speed] = {
                                "completed_step": completed,
                                "organism_id": oid,
                                "speed": speed,
                                "start": [None if nx is None else nx - dx, None if ny is None else ny - dy],
                                "end": [nx, ny],
                                "target": [tx, ty],
                                "movement_energy_cost": cost,
                                "resource_consumed_same_step": consumption_by_step_id.get((completed, oid), 0),
                                "energy_before_step": recorder.energy_by_step.get(completed - 1, {}).get(oid),
                                "energy_after_step": recorder.energy_by_step.get(completed, {}).get(oid),
                            }
        if applied.process_name == "Reproduction" and len(reproduction_events) < 20:
            reproduction_events.append({
                "event_step_index": applied.event_step_index,
                "event_type": type(event).__name__,
                "event_repr": repr(event),
            })

    founder_reproduction = {LOW_SPEED: [], HIGH_SPEED: []}
    all_reproduction = {LOW_SPEED: [], HIGH_SPEED: []}
    deaths = {LOW_SPEED: 0, HIGH_SPEED: 0}
    death_causes: dict[int, dict[str, int]] = {LOW_SPEED: {}, HIGH_SPEED: {}}
    for record in ecology.pedigree_recorder.records:
        speed = recorder.speed_by_id.get(record.organism_id)
        if speed not in (LOW_SPEED, HIGH_SPEED):
            continue
        all_reproduction[speed].append(record.realized_reproductive_success)
        if record.is_founder:
            founder_reproduction[speed].append(record.realized_reproductive_success)
        if not record.is_alive:
            deaths[speed] += 1
            cause = record.death_cause or "unknown"
            death_causes[speed][cause] = death_causes[speed].get(cause, 0) + 1

    extinction_step = next((x["step"] for x in population_history if x["population"] == 0), None)
    last_nonzero = next((x for x in reversed(genetic_history) if x["population"] > 0), genetic_history[0])
    return {
        "label": label,
        "seed": seed,
        "final_population": population_history[-1]["population"],
        "extinction_step": extinction_step,
        "last_nonzero_step": last_nonzero["step"],
        "last_nonzero_high_allele_frequency": last_nonzero["high_allele_frequency"],
        "genetic_history": genetic_history,
        "population_history": population_history,
        "mechanism": {
            "consumption": {str(k): v for k, v in consumption.items()},
            "targeted_moves": {str(k): v for k, v in targeted_moves.items()},
            "movement_energy": {str(k): v for k, v in movement_energy.items()},
            "metabolism_energy": {str(k): v for k, v in metabolism_energy.items()},
            "founder_reproductive_success": {str(k): _dist(v) for k, v in founder_reproduction.items()},
            "all_reproductive_success": {str(k): _dist(v) for k, v in all_reproduction.items()},
            "deaths": {str(k): v for k, v in deaths.items()},
            "death_causes": {str(k): v for k, v in death_causes.items()},
        },
        "movement_examples": {str(k): v for k, v in movement_examples.items()},
        "reproduction_examples": reproduction_events,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("outputs/b3-analysis/b3-scenario-search.json"))
    args = parser.parse_args()
    results = []
    for label, (deposits, placement) in _environment_specs().items():
        for seed in SEEDS:
            results.append(_run_one(label=label, seed=seed, deposits=deposits, placement=placement))
    payload = {
        "analysis_only": True,
        "analysis_round": "single_oasis",
        "focal_trait": MAX_SPEED,
        "low_speed": LOW_SPEED,
        "high_speed": HIGH_SPEED,
        "seeds": list(SEEDS),
        "max_steps": MAX_STEPS,
        "founders": {"population": 20, "high_allele_frequency": 0.5, "mutation_probability_ppm": 0, "mating_radius": 3},
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
