#!/usr/bin/env python3
"""Microbenchmark transactional state-copy operations with pyperf."""

from __future__ import annotations

import pyperf

from evo_engine.presets import ReferenceEcologyConfig, build_reference_simulation


def main() -> None:
    """Benchmark fixed reference SimulationState and WorldState copy operations."""
    simulation = build_reference_simulation(ReferenceEcologyConfig())
    state = simulation.state
    world = state.domain_state

    runner = pyperf.Runner(
        metadata={
            "scenario": "reference-ecology-initial-state",
            "population_size": len(world.organisms),
            "resource_cells": len(world.resources),
        }
    )
    runner.bench_func("simulation_state.copy", state.copy)
    runner.bench_func("world_state.copy", world.copy)


if __name__ == "__main__":
    main()
