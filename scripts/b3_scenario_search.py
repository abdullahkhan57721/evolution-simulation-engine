"""Run bounded B3 environment-dependent selection experiments.

This script is temporary analysis instrumentation. It is intentionally not a
public package surface or flagship implementation.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import attrs

from evo_engine.ecology import (
    PatchyResourcePlacement,
    ResourcePatch,
    UniformResourcePlacement,
)
from evo_engine.engine import Simulation
from evo_engine.genetics import GENETIC_ARCHITECTURE, MAX_SPEED
from evo_engine.presets.reference_ecology.config import ReferenceEcologyConfig
from evo_engine.presets.reference_ecology.genetics import (
    build_balanced_reference_trait_world,
)
from evo_engine.presets.reference_ecology.observable import build_reference_ecology
from evo_engine.world import WorldState

LOW_SPEED = 1
HIGH_SPEED = 4
SEEDS = (11, 23, 37, 41, 59, 73, 89, 101)
MAX_STEPS = 40


class IndividualStateRecorder:
    """Record analysis-only per-organism speed, energy, and position by step."""

    def __init__(self) -> None:
        self.speed_by_id: dict[int, int] = {}
        self.energy_by_step: dict[int, dict[int, int]] = {}
        self.position_by_step: dict[int, dict[int, tuple[int, int]]] = {}

    def should_observe(self, world_state: WorldState, *, step_index: int) -> bool:
        """Observe every committed state offered by the engine."""
        del world_state, step_index
        return True

    def observe(self, world_state: WorldState, *, step_index: int) -> None:
        """Store immutable scalar values needed only for experiment analysis."""
        energies: dict[int, int] = {}
        positions: dict[int, tuple[int, int]] = {}
        for organism_id, organism in world_state.organisms.items():
            self.speed_by_id[organism_id] = organism.genetic_phenotype.int_value(
                MAX_SPEED
            )
            energies[organism_id] = organism.energy
            positions[organism_id] = (organism.x, organism.y)
        self.energy_by_step[step_index] = energies
        self.position_by_step[step_index] = positions


def _environment_specs() -> dict[str, tuple[int, object]]:
    near_compact = PatchyResourcePlacement(
        patches=(
            ResourcePatch(center_x=2, center_y=5, radius=1),
            ResourcePatch(center_x=9, center_y=5, radius=1),
        )
    )
    farther_compact = PatchyResourcePlacement(
        patches=(
            ResourcePatch(center_x=2, center_y=7, radius=1),
            ResourcePatch(center_x=9, center_y=7, radius=1),
        )
    )
    near_broad = PatchyResourcePlacement(
        patches=(
            ResourcePatch(center_x=2, center_y=5, radius=2),
            ResourcePatch(center_x=9, center_y=5, radius=2),
        )
    )
    return {
        "uniform_d8": (8, UniformResourcePlacement()),
        "patch_y5_r1_d8": (8, near_compact),
        "uniform_d16": (16, UniformResourcePlacement()),
        "patch_y5_r1_d16": (16, near_compact),
        "uniform_d32": (32, UniformResourcePlacement()),
        "patch_y5_r1_d32": (32, near_compact),
        "patch_y7_r1_d16": (16, farther_compact),
        "patch_y5_r2_d16": (16, near_broad),
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
        mating_radius=1,
        traits=attrs.evolve(
            baseline.traits,
            attack_strength=0,
            defense=1,
        ),
    )


def _run_one(*, label: str, seed: int, deposits: int, placement: object) -> dict[str, Any]:
    recorder = IndividualStateRecorder()
    config = _config(seed=seed, deposits=deposits, placement=placement)
    ecology = build_reference_ecology(config, additional_observers=(recorder,))
    architecture = ecology.simulation.context.require(GENETIC_ARCHITECTURE)
    world = build_balanced_reference_trait_world(
        architecture,
        trait_name=MAX_SPEED,
        variant_values=(LOW_SPEED, HIGH_SPEED),
        config=config,
    )
    simulation = Simulation(
        initial_domain_state=world,
        seed=seed,
        context=ecology.simulation.context,
    )
    ecology.engine.run(simulation)

    genetic_history = []
    for observation in ecology.genetic_recorder.observations:
        locus = observation.locus(MAX_SPEED)
        genetic_history.append(
            {
                "step": observation.step_index,
                "population": observation.population_size,
                "high_allele_frequency": locus.allele_frequency(HIGH_SPEED),
                "genotypes": [
                    {
                        "alleles": list(item.allele_values),
                        "count": item.count,
                        "frequency": item.frequency,
                    }
                    for item in locus.genotypes
                ],
            }
        )

    population_history = []
    for observation in ecology.recorder.observations:
        speed_summary = next(
            item for item in observation.traits if item.trait_name == MAX_SPEED
        )
        population_history.append(
            {
                "step": observation.step_index,
                "population": observation.population_size,
                "resources": observation.total_resources,
                "mean_energy": observation.energy.mean,
                "mean_speed": speed_summary.summary.mean,
                "speed_counts": [list(item) for item in speed_summary.value_counts],
            }
        )

    movement = {LOW_SPEED: _event_bucket(), HIGH_SPEED: _event_bucket()}
    metabolism = {LOW_SPEED: _event_bucket(), HIGH_SPEED: _event_bucket()}
    consumption = {LOW_SPEED: _event_bucket(), HIGH_SPEED: _event_bucket()}
    movement_examples: dict[int, dict[str, Any] | None] = {
        LOW_SPEED: None,
        HIGH_SPEED: None,
    }

    consumption_by_step_id: dict[tuple[int, int], int] = {}
    for applied in ecology.event_recorder.events:
        event = applied.event
        organism_id = getattr(event, "organism_id", None)
        if applied.process_name != "ResourceConsumption" or type(organism_id) is not int:
            continue
        amount = getattr(event, "amount", 0)
        if type(amount) is int:
            consumption_by_step_id[(applied.event_step_index + 1, organism_id)] = amount

    for applied in ecology.event_recorder.events:
        event = applied.event
        organism_id = getattr(event, "organism_id", None)
        if type(organism_id) is not int:
            continue
        speed = recorder.speed_by_id.get(organism_id)
        if speed not in (LOW_SPEED, HIGH_SPEED):
            continue

        if applied.process_name == "Movement":
            dx = getattr(event, "dx", 0)
            dy = getattr(event, "dy", 0)
            energy_cost = getattr(event, "energy_cost", 0)
            target_x = getattr(event, "target_x", None)
            target_y = getattr(event, "target_y", None)
            distance = math.sqrt(dx * dx + dy * dy)
            bucket = movement[speed]
            bucket["events"] += 1
            bucket["amount"] += distance
            bucket["energy_cost"] += energy_cost
            if target_x is not None:
                bucket["targeted_events"] += 1

            if target_x is not None and movement_examples[speed] is None:
                completed_step = applied.event_step_index + 1
                new_x = getattr(event, "new_x", None)
                new_y = getattr(event, "new_y", None)
                start_x = None if new_x is None else new_x - dx
                start_y = None if new_y is None else new_y - dy
                movement_examples[speed] = {
                    "completed_step": completed_step,
                    "organism_id": organism_id,
                    "speed": speed,
                    "start": [start_x, start_y],
                    "end": [new_x, new_y],
                    "target": [target_x, target_y],
                    "distance": distance,
                    "movement_energy_cost": energy_cost,
                    "resource_consumed_same_step": consumption_by_step_id.get(
                        (completed_step, organism_id), 0
                    ),
                    "energy_before_step": recorder.energy_by_step.get(
                        completed_step - 1, {}
                    ).get(organism_id),
                    "energy_after_step": recorder.energy_by_step.get(
                        completed_step, {}
                    ).get(organism_id),
                }
        elif applied.process_name == "Metabolism":
            cost = getattr(event, "energy_cost", 0)
            bucket = metabolism[speed]
            bucket["events"] += 1
            bucket["energy_cost"] += cost
        elif applied.process_name == "ResourceConsumption":
            amount = getattr(event, "amount", 0)
            bucket = consumption[speed]
            bucket["events"] += 1
            bucket["amount"] += amount

    founder_reproduction = {LOW_SPEED: [], HIGH_SPEED: []}
    deaths = {LOW_SPEED: 0, HIGH_SPEED: 0}
    death_causes: dict[int, dict[str, int]] = {LOW_SPEED: {}, HIGH_SPEED: {}}
    for record in ecology.pedigree_recorder.records:
        speed = recorder.speed_by_id.get(record.organism_id)
        if speed not in (LOW_SPEED, HIGH_SPEED):
            continue
        if record.is_founder:
            founder_reproduction[speed].append(record.realized_reproductive_success)
        if not record.is_alive:
            deaths[speed] += 1
            cause = record.death_cause or "unknown"
            death_causes[speed][cause] = death_causes[speed].get(cause, 0) + 1

    final_genetic = genetic_history[-1]
    final_population = population_history[-1]["population"]
    extinction_step = next(
        (item["step"] for item in population_history if item["population"] == 0),
        None,
    )

    return {
        "label": label,
        "seed": seed,
        "deposits_per_step": deposits,
        "generated_resources_per_step": deposits * config.resource_generation_amount,
        "final_population": final_population,
        "extinction_step": extinction_step,
        "final_high_allele_frequency": final_genetic["high_allele_frequency"],
        "genetic_history": genetic_history,
        "population_history": population_history,
        "mechanism": {
            "movement": _finalize_buckets(movement),
            "metabolism": _finalize_buckets(metabolism),
            "consumption": _finalize_buckets(consumption),
            "deaths": {str(key): value for key, value in deaths.items()},
            "death_causes": {
                str(key): value for key, value in death_causes.items()
            },
            "founder_reproductive_success": {
                str(key): _integer_distribution(values)
                for key, values in founder_reproduction.items()
            },
        },
        "movement_examples": {
            str(key): value for key, value in movement_examples.items()
        },
    }


def _event_bucket() -> dict[str, float | int]:
    return {
        "events": 0,
        "targeted_events": 0,
        "amount": 0.0,
        "energy_cost": 0,
    }


def _finalize_buckets(
    buckets: dict[int, dict[str, float | int]],
) -> dict[str, dict[str, float | int | None]]:
    result: dict[str, dict[str, float | int | None]] = {}
    for speed, bucket in buckets.items():
        events = int(bucket["events"])
        result[str(speed)] = {
            **bucket,
            "mean_amount_per_event": (
                float(bucket["amount"]) / events if events else None
            ),
            "mean_energy_cost_per_event": (
                float(bucket["energy_cost"]) / events if events else None
            ),
        }
    return result


def _integer_distribution(values: list[int]) -> dict[str, float | int | None]:
    if not values:
        return {"count": 0, "mean": None, "total": 0}
    return {
        "count": len(values),
        "mean": sum(values) / len(values),
        "total": sum(values),
    }


def main() -> None:
    """Run the bounded environment set and write deterministic JSON evidence."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/performance/b3-scenario-search.json"),
    )
    args = parser.parse_args()

    results = []
    for label, (deposits, placement) in _environment_specs().items():
        for seed in SEEDS:
            results.append(
                _run_one(
                    label=label,
                    seed=seed,
                    deposits=deposits,
                    placement=placement,
                )
            )

    payload = {
        "analysis_only": True,
        "focal_trait": MAX_SPEED,
        "low_speed": LOW_SPEED,
        "high_speed": HIGH_SPEED,
        "seeds": list(SEEDS),
        "max_steps": MAX_STEPS,
        "founders": {
            "population": 20,
            "high_allele_frequency": 0.5,
            "mutation_probability_ppm": 0,
            "predation_isolated_by_attack_defense": True,
        },
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
