"""Tests for the nonbiological general-evolution vertical slice."""

from __future__ import annotations

import ast
import subprocess
import sys
from collections import Counter
from pathlib import Path

from examples.nonbiological_evolution import (
    AMPLIFY,
    BROADCAST_WEIGHT,
    DEFAULT_SEED,
    DEFAULT_STEPS,
    InformationNetwork,
    StrategyCharacteristics,
    build_nonbiological_evolution,
)

EXAMPLE_PATH = Path(__file__).parents[2] / "examples/nonbiological_evolution.py"
ALLOWED_EVO_ENGINE_IMPORTS = (
    "evo_engine.configuration",
    "evo_engine.engine",
    "evo_engine.evolution",
    "evo_engine.propagation",
    "evo_engine.resolvers",
    "evo_engine.telemetry",
)


def _run_example(seed: int = DEFAULT_SEED):
    example = build_nonbiological_evolution(seed=seed)
    initial_state = example.compiled.simulation.state.domain_state
    assert isinstance(initial_state, InformationNetwork)
    initial_ids = tuple(initial_state.nodes)
    initial_composition = initial_state.composition()

    example.compiled.engine.run(example.compiled.simulation)

    final_state = example.compiled.simulation.state.domain_state
    assert isinstance(final_state, InformationNetwork)
    return example, initial_ids, initial_composition, final_state


def test_nonbiological_evolution_changes_transmissible_composition() -> None:
    """Test expression, differential propagation, and variation end to end."""
    example, initial_ids, initial_composition, final_state = _run_example()
    snapshots = example.recorder.snapshots
    events = example.recorder.events
    source_counts = Counter(event.source_state for event in events)

    assert example.compiled.simulation.state.step_index == DEFAULT_STEPS
    assert tuple(final_state.nodes) == initial_ids
    assert initial_composition == {"amplify": 3, "retain": 9}
    assert final_state.composition() != initial_composition
    assert final_state.composition()[AMPLIFY] > initial_composition[AMPLIFY]
    assert [snapshot.step_index for snapshot in snapshots] == list(
        range(DEFAULT_STEPS + 1)
    )
    assert snapshots[0].composition == tuple(initial_composition.items())
    assert snapshots[-1].composition == tuple(final_state.composition().items())
    assert source_counts[AMPLIFY] > source_counts.total() / 2
    assert any(event.source_state != event.propagated_state for event in events)


def test_transmissible_tokens_express_differential_operational_weight() -> None:
    """Test propagated variants expose distinct operative characteristics."""
    example = build_nonbiological_evolution()
    network = example.compiled.simulation.state.domain_state
    assert isinstance(network, InformationNetwork)
    characteristics = StrategyCharacteristics()

    amplify_weight = characteristics.value_for(
        network.nodes[0],
        BROADCAST_WEIGHT,
        context=network,
    )
    retain_weight = characteristics.value_for(
        network.nodes[3],
        BROADCAST_WEIGHT,
        context=network,
    )

    assert amplify_weight == 3
    assert retain_weight == 1


def test_same_seed_reproduces_the_same_evolutionary_history() -> None:
    """Test fixed initial state and seed reproduce all committed outcomes."""
    first, _, _, first_state = _run_example()
    second, _, _, second_state = _run_example()

    assert first.recorder.snapshots == second.recorder.snapshots
    assert first.recorder.events == second.recorder.events
    assert first_state.composition() == second_state.composition()


def test_example_uses_only_generic_evo_engine_packages() -> None:
    """Test the runnable slice stays independent of domain specializations."""
    tree = ast.parse(EXAMPLE_PATH.read_text())
    imported_modules: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)

    evo_engine_imports = {
        module for module in imported_modules if module.startswith("evo_engine")
    }

    assert all(
        any(
            module == allowed or module.startswith(f"{allowed}.")
            for allowed in ALLOWED_EVO_ENGINE_IMPORTS
        )
        for module in evo_engine_imports
    )


def test_runnable_example_prints_stable_changed_composition() -> None:
    """Test the documented command exposes a deterministic concise summary."""
    command = [sys.executable, str(EXAMPLE_PATH)]
    first = subprocess.run(command, check=True, capture_output=True, text=True)
    second = subprocess.run(command, check=True, capture_output=True, text=True)

    assert first.stdout == second.stdout
    assert "Seed: 84" in first.stdout
    assert "Completed steps: 6" in first.stdout
    assert "Initial composition: amplify=3, retain=9" in first.stdout
    assert "Final composition:" in first.stdout
    assert "Final composition: amplify=3, retain=9" not in first.stdout
