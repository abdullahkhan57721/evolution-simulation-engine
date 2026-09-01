"""Run reproducible multi-seed experiments with the reference ecology."""

from __future__ import annotations

import json
import platform
from collections import Counter
from importlib import metadata

import attrs

from evo_engine.genetics import GENETIC_ARCHITECTURE
from evo_engine.observation import (
    GeneticCompositionObservation,
    IndividualLifeHistory,
    PopulationObservation,
)
from evo_engine.presets import ReferenceEcologyConfig, build_reference_ecology
from evo_engine.validation import validators

_PACKAGE_NAME = "evolution-simulation-engine"


@attrs.frozen(slots=True, kw_only=True)
class RunMetadata:
    """Record information required to identify and reproduce one replicate."""

    seed: int
    engine_version: str
    python_version: str
    config_json: str
    trait_names: tuple[str, ...]
    locus_names: tuple[str, ...]
    completed_steps: int

    def __attrs_post_init__(self) -> None:
        """Validate metadata values."""
        validators.validate_int(self.seed, name="seed")
        _validate_nonempty_string(self.engine_version, name="engine_version")
        _validate_nonempty_string(self.python_version, name="python_version")
        _validate_nonempty_string(self.config_json, name="config_json")
        validators.validate_tuple(self.trait_names, name="trait_names")
        validators.validate_tuple(self.locus_names, name="locus_names")
        validators.validate_int_ge(
            self.completed_steps, bound=0, name="completed_steps"
        )


@attrs.frozen(slots=True, kw_only=True)
class ReferenceReplicateResult:
    """Immutable measurements from one reference-ecology replicate."""

    metadata: RunMetadata
    final_population_size: int
    final_carcass_count: int
    final_total_resources: int
    population_history: tuple[PopulationObservation, ...]
    genetic_history: tuple[GeneticCompositionObservation, ...]
    life_histories: tuple[IndividualLifeHistory, ...]
    event_counts: tuple[tuple[str, int], ...]

    def __attrs_post_init__(self) -> None:
        validators.validate_int_ge(
            self.final_population_size, bound=0, name="final_population_size"
        )
        validators.validate_int_ge(
            self.final_carcass_count, bound=0, name="final_carcass_count"
        )
        validators.validate_int_ge(
            self.final_total_resources, bound=0, name="final_total_resources"
        )
        validators.validate_tuple(self.population_history, name="population_history")
        validators.validate_tuple(self.genetic_history, name="genetic_history")
        validators.validate_tuple(self.life_histories, name="life_histories")
        validators.validate_tuple(self.event_counts, name="event_counts")

    @property
    def seed(self) -> int:
        return self.metadata.seed

    @property
    def total_births(self) -> int:
        return sum(not history.is_founder for history in self.life_histories)

    @property
    def total_deaths(self) -> int:
        return sum(not history.is_alive for history in self.life_histories)

    def event_count(self, process_name: str) -> int:
        validated_name = _validate_nonempty_string(process_name, name="process_name")
        for name, count in self.event_counts:
            if name == validated_name:
                return count
        return 0


@attrs.frozen(slots=True, kw_only=True)
class ReferenceExperimentResult:
    """Immutable collection of independent reference-ecology replicates."""

    replicates: tuple[ReferenceReplicateResult, ...]

    def __attrs_post_init__(self) -> None:
        validators.validate_tuple(self.replicates, name="replicates")
        if not self.replicates:
            raise ValueError("replicates must not be empty.")
        seeds = tuple(replicate.seed for replicate in self.replicates)
        if len(seeds) != len(set(seeds)):
            raise ValueError("replicates must have unique seeds.")

    @property
    def seeds(self) -> tuple[int, ...]:
        return tuple(replicate.seed for replicate in self.replicates)

    def replicate(self, seed: int) -> ReferenceReplicateResult:
        validated_seed = validators.validate_int(seed, name="seed")
        for replicate in self.replicates:
            if replicate.seed == validated_seed:
                return replicate
        raise KeyError(f"No replicate recorded for seed {validated_seed}.")


def run_reference_replicates(
    config: ReferenceEcologyConfig | None = None,
    *,
    seeds: tuple[int, ...],
) -> ReferenceExperimentResult:
    resolved_config = config if config is not None else ReferenceEcologyConfig()
    _validate_seeds(seeds)
    return ReferenceExperimentResult(
        replicates=tuple(
            _run_reference_replicate(attrs.evolve(resolved_config, seed=seed))
            for seed in seeds
        )
    )


def _run_reference_replicate(
    config: ReferenceEcologyConfig,
) -> ReferenceReplicateResult:
    ecology = build_reference_ecology(config)
    ecology.engine.run(ecology.simulation)
    world = ecology.simulation.state.domain_state
    architecture = ecology.simulation.context.require(GENETIC_ARCHITECTURE)
    event_counts = Counter(
        event.process_name for event in ecology.event_recorder.events
    )
    return ReferenceReplicateResult(
        metadata=RunMetadata(
            seed=config.seed,
            engine_version=_engine_version(),
            python_version=platform.python_version(),
            config_json=_canonical_config_json(config),
            trait_names=tuple(sorted(architecture.trait_names)),
            locus_names=tuple(locus.name for locus in architecture.loci),
            completed_steps=ecology.simulation.state.step_index,
        ),
        final_population_size=len(world.organisms),
        final_carcass_count=len(world.carcasses),
        final_total_resources=sum(world.resources.values()),
        population_history=ecology.recorder.observations,
        genetic_history=ecology.genetic_recorder.observations,
        life_histories=ecology.pedigree_recorder.records,
        event_counts=tuple(sorted(event_counts.items())),
    )


def _canonical_config_json(config: ReferenceEcologyConfig) -> str:
    return json.dumps(attrs.asdict(config), sort_keys=True, separators=(",", ":"))


def _engine_version() -> str:
    try:
        return metadata.version(_PACKAGE_NAME)
    except metadata.PackageNotFoundError:
        return "unknown"


def _validate_seeds(seeds: tuple[int, ...]) -> None:
    validators.validate_tuple(seeds, name="seeds")
    if not seeds:
        raise ValueError("seeds must not be empty.")
    seen: set[int] = set()
    for index, seed in enumerate(seeds):
        validated = validators.validate_int(seed, name=f"seeds[{index}]")
        if validated in seen:
            raise ValueError(f"seeds must not contain duplicate seed {validated}.")
        seen.add(validated)


def _validate_nonempty_string(value: object, *, name: str) -> str:
    validated = validators.validate_str(value, name=name)
    if not validated.strip():
        raise ValueError(f"{name} must not be empty or whitespace-only.")
    return validated
