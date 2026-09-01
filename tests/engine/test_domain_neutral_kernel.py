"""Architecture tests for the domain-neutral simulation kernel boundary."""

from __future__ import annotations

import ast
from collections.abc import Iterable
from pathlib import Path

from evo_engine.engine import (
    MaxSteps,
    SequentialStepCoordinator,
    Simulation,
    SimulationEngine,
    StageCoordinator,
)
from evo_engine.resolvers import AcceptAll
from tests.engine.helpers import CounterState, IncrementProcess

_DOMAIN_MODULE_PREFIXES = (
    "evo_engine.behavior",
    "evo_engine.biology",
    "evo_engine.characteristics",
    "evo_engine.development",
    "evo_engine.ecology",
    "evo_engine.energetics",
    "evo_engine.experiments",
    "evo_engine.feeding",
    "evo_engine.genetics",
    "evo_engine.growth",
    "evo_engine.life_history",
    "evo_engine.observation",
    "evo_engine.predation",
    "evo_engine.presets",
    "evo_engine.processes",
    "evo_engine.reproduction",
    "evo_engine.spatial",
    "evo_engine.world",
)
_DOMAIN_TEST_HELPERS = ("tests.helpers",)
_DOMAIN_IDENTIFIER_FRAGMENTS = (
    "organism",
    "genetic",
    "genome",
    "phenotype",
    "mating",
    "reproduction",
    "offspring",
    "predator",
    "prey",
    "starvation",
    "metabolism",
    "carcass",
    "body_mass",
    "energy",
    "aging",
    "mutation",
    "world",
)
_KERNEL_SOURCE_PATHS = (
    Path("src/evo_engine/engine"),
    Path("src/evo_engine/configuration"),
    Path("src/evo_engine/telemetry"),
    Path("src/evo_engine/access.py"),
    Path("src/evo_engine/admission.py"),
    Path("src/evo_engine/departure.py"),
    Path("src/evo_engine/production.py"),
    Path("src/evo_engine/propagation.py"),
    Path("src/evo_engine/reference.py"),
    Path("src/evo_engine/validation"),
    Path("src/evo_engine/resolvers/_preference_order.py"),
    Path("src/evo_engine/resolvers/accept_all.py"),
)
_KERNEL_TEST_PATHS = (
    Path("tests/engine"),
    Path("tests/configuration"),
    Path("tests/telemetry"),
    Path("tests/test_access.py"),
    Path("tests/test_admission.py"),
    Path("tests/test_departure.py"),
    Path("tests/test_production.py"),
    Path("tests/test_propagation.py"),
    Path("tests/test_reference.py"),
    Path("tests/validation"),
    Path("tests/resolvers/test_generic_preference_order.py"),
    Path("tests/resolvers/test_preference_order_import_boundary.py"),
)
_KERNEL_TOOLING_PATHS = (
    Path("scripts/profile_kernel.py"),
    Path("scripts/benchmark_state_copy.py"),
)


def test_kernel_runs_nonbiological_transactional_state() -> None:
    """Test core execution works with an arbitrary copyable state object."""
    simulation = Simulation(
        initial_domain_state=CounterState(),
        seed=7,
        selection_policy="priority",
    )
    engine = SimulationEngine(
        step_coordinator=SequentialStepCoordinator(
            stages=(
                StageCoordinator(
                    processes=(IncrementProcess(),),
                    resolver=AcceptAll(),
                ),
            )
        ),
        stopping_condition=MaxSteps(max_steps=3),
    )

    engine.run(simulation)

    assert simulation.state.domain_state.value == 3
    assert simulation.state.step_index == 3
    assert simulation.context.require("selection_policy") == "priority"


def test_kernel_source_does_not_import_modeled_domains() -> None:
    """Test every production kernel module stays above modeled domains."""
    violations = _import_violations(
        _python_files(_KERNEL_SOURCE_PATHS),
        forbidden_prefixes=_DOMAIN_MODULE_PREFIXES,
    )

    assert violations == []


def test_kernel_source_uses_domain_neutral_identifiers() -> None:
    """Test production kernel identifiers avoid modeled-domain vocabulary."""
    violations = _identifier_violations(_python_files(_KERNEL_SOURCE_PATHS))

    assert violations == []


def test_kernel_tests_do_not_import_modeled_domains_or_domain_helpers() -> None:
    """Test kernel tests cannot normalize domain coupling through fixtures."""
    violations = _import_violations(
        _python_files(_KERNEL_TEST_PATHS),
        forbidden_prefixes=(
            *_DOMAIN_MODULE_PREFIXES,
            *_DOMAIN_TEST_HELPERS,
        ),
    )

    assert violations == []


def test_kernel_tests_use_domain_neutral_identifiers() -> None:
    """Test kernel-facing fixtures avoid modeled-domain vocabulary."""
    guard_path = Path(__file__)
    violations = _identifier_violations(
        path for path in _python_files(_KERNEL_TEST_PATHS) if path != guard_path
    )

    assert violations == []


def test_kernel_tooling_does_not_use_removed_world_state_attribute() -> None:
    """Test kernel-facing tooling uses the canonical domain_state envelope API."""
    violations = _attribute_violations(
        _python_files(_KERNEL_TOOLING_PATHS),
        forbidden_attributes=("world",),
    )

    assert violations == []


def _python_files(paths: Iterable[Path]) -> tuple[Path, ...]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(sorted(path.rglob("*.py")))
        elif path.exists():
            files.append(path)
    return tuple(files)


def _import_violations(
    paths: Iterable[Path],
    *,
    forbidden_prefixes: tuple[str, ...],
) -> list[str]:
    violations: list[str] = []

    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            for module in _imported_modules(node):
                if module.startswith(forbidden_prefixes):
                    violations.append(f"{path}: imports {module}")

    return violations


def _identifier_violations(paths: Iterable[Path]) -> list[str]:
    violations: list[str] = []

    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for identifier in _declared_identifiers(tree):
            lowered = identifier.lower()
            for fragment in _DOMAIN_IDENTIFIER_FRAGMENTS:
                if fragment in lowered:
                    violations.append(f"{path}: identifier {identifier!r}")
                    break

    return violations


def _attribute_violations(
    paths: Iterable[Path],
    *,
    forbidden_attributes: tuple[str, ...],
) -> list[str]:
    violations: list[str] = []
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in forbidden_attributes:
                violations.append(f"{path}: attribute {node.attr!r}")
    return violations


def _imported_modules(node: ast.AST) -> tuple[str, ...]:
    if isinstance(node, ast.Import):
        return tuple(alias.name for alias in node.names)
    if isinstance(node, ast.ImportFrom) and node.module is not None:
        return (node.module,)
    return ()


def _declared_identifiers(tree: ast.AST) -> tuple[str, ...]:
    identifiers: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            identifiers.append(node.id)
        elif isinstance(node, ast.Attribute):
            identifiers.append(node.attr)
        elif isinstance(node, ast.arg):
            identifiers.append(node.arg)
        elif isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            identifiers.append(node.name)

    return tuple(identifiers)
