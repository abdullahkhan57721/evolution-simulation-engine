"""Record pedigree, mortality, and individual reproductive success."""

from __future__ import annotations

import attrs

from evo_engine.telemetry import (
    AppliedEvent,
    MortalityEvent,
    ParentageEvent,
    StepTelemetry,
)
from evo_engine.validation import attrs_validators, validators
from evo_engine.world import WorldState


@attrs.frozen(slots=True, kw_only=True)
class IndividualLifeHistory:
    """Immutable observed life history for one organism.

    ``realized_reproductive_success`` is the observed number of offspring
    produced so far. ``lifetime_reproductive_success`` is available only after
    a recorded biological death, because the reproductive success of a living
    organism is right-censored rather than a completed lifetime quantity.

    Attributes:
        organism_id: Permanent organism ID.
        parent_ids: Biological parent IDs, empty when parentage is unknown.
        is_founder: Whether the organism belonged to the recorder's baseline
            population.
        entry_step: Step at which the organism first entered observation.
        entry_age: Age at entry when known.
        birth_step: Inferred or observed birth step when known.
        death_step: Completed step in which biological death occurred.
        death_cause: Unqualified process class name causing death.
        death_process_type: Fully qualified process class name causing death.
        offspring_ids: Observed biological offspring IDs in birth order.
    """

    organism_id: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    parent_ids: tuple[int, ...] = attrs.field(factory=tuple)
    is_founder: bool = attrs.field(
        default=False,
        validator=attrs_validators.validate_bool,
    )
    entry_step: int = attrs.field(
        default=0,
        validator=attrs_validators.validate_int_ge(0),
    )
    entry_age: int | None = attrs.field(default=None)
    birth_step: int | None = attrs.field(default=None)
    death_step: int | None = attrs.field(default=None)
    death_cause: str | None = attrs.field(default=None)
    death_process_type: str | None = attrs.field(default=None)
    offspring_ids: tuple[int, ...] = attrs.field(factory=tuple)

    def __attrs_post_init__(self) -> None:
        """Validate pedigree and life-history invariants."""
        _validate_unique_ids(self.parent_ids, name="parent_ids")
        _validate_unique_ids(self.offspring_ids, name="offspring_ids")

        if self.organism_id in self.parent_ids:
            raise ValueError("An organism cannot be its own parent.")
        if self.organism_id in self.offspring_ids:
            raise ValueError("An organism cannot be its own offspring.")

        if self.entry_age is not None:
            validators.validate_int_ge(
                self.entry_age,
                bound=0,
                name="entry_age",
            )
        if self.birth_step is not None:
            validators.validate_int_ge(
                self.birth_step,
                bound=0,
                name="birth_step",
            )
            if self.birth_step > self.entry_step:
                raise ValueError("birth_step cannot be later than entry_step.")

        if self.death_step is None:
            if self.death_cause is not None or self.death_process_type is not None:
                raise ValueError(
                    "death_cause and death_process_type require death_step."
                )
        else:
            validators.validate_int_ge(
                self.death_step,
                bound=self.entry_step,
                name="death_step",
            )
            _validate_optional_nonempty_string(
                self.death_cause,
                name="death_cause",
                required=True,
            )
            _validate_optional_nonempty_string(
                self.death_process_type,
                name="death_process_type",
                required=True,
            )

    @property
    def is_alive(self) -> bool:
        """Return whether no biological death has been recorded."""
        return self.death_step is None

    @property
    def offspring_count(self) -> int:
        """Return the number of observed biological offspring."""
        return len(self.offspring_ids)

    @property
    def realized_reproductive_success(self) -> int:
        """Return observed direct reproductive success so far."""
        return self.offspring_count

    @property
    def lifetime_reproductive_success(self) -> int | None:
        """Return completed lifetime offspring count, or None while alive."""
        if self.is_alive:
            return None
        return self.offspring_count

    @property
    def lifespan_steps(self) -> int | None:
        """Return observed lifespan in steps when birth and death are known."""
        if self.birth_step is None or self.death_step is None:
            return None
        return self.death_step - self.birth_step


@attrs.define(slots=True, kw_only=True)
class _MutableLifeHistory:
    organism_id: int
    parent_ids: tuple[int, ...]
    is_founder: bool
    entry_step: int
    entry_age: int | None
    birth_step: int | None
    death_step: int | None = None
    death_cause: str | None = None
    death_process_type: str | None = None
    offspring_ids: list[int] = attrs.field(factory=list)

    def snapshot(self) -> IndividualLifeHistory:
        return IndividualLifeHistory(
            organism_id=self.organism_id,
            parent_ids=self.parent_ids,
            is_founder=self.is_founder,
            entry_step=self.entry_step,
            entry_age=self.entry_age,
            birth_step=self.birth_step,
            death_step=self.death_step,
            death_cause=self.death_cause,
            death_process_type=self.death_process_type,
            offspring_ids=tuple(self.offspring_ids),
        )


@attrs.define(slots=True, kw_only=True)
class PedigreeRecorder:
    """Record pedigree, death cause, lifespan, and direct reproductive success.

    The recorder structurally implements both the state ``Observer`` interface
    and ``TelemetryObserver``. Attach the same instance to both collections so
    it first registers the baseline population and then consumes every committed
    step's event telemetry.
    """

    _histories: dict[int, _MutableLifeHistory] = attrs.field(
        factory=dict,
        init=False,
        repr=False,
    )
    _initialized: bool = attrs.field(
        default=False,
        init=False,
        repr=False,
    )
    _last_telemetry_step: int | None = attrs.field(
        default=None,
        init=False,
        repr=False,
    )

    @property
    def records(self) -> tuple[IndividualLifeHistory, ...]:
        """Return all individual histories ordered by organism ID."""
        return tuple(
            self._histories[organism_id].snapshot()
            for organism_id in sorted(self._histories)
        )

    @property
    def founder_ids(self) -> tuple[int, ...]:
        """Return baseline founder IDs in organism-ID order."""
        return tuple(
            record.organism_id for record in self.records if record.is_founder
        )

    @property
    def living_ids(self) -> tuple[int, ...]:
        """Return IDs without a recorded biological death."""
        return tuple(record.organism_id for record in self.records if record.is_alive)

    @property
    def dead_ids(self) -> tuple[int, ...]:
        """Return IDs with a recorded biological death."""
        return tuple(
            record.organism_id for record in self.records if not record.is_alive
        )

    def record(self, organism_id: int) -> IndividualLifeHistory:
        """Return one organism's immutable life-history record.

        Args:
            organism_id: Permanent organism ID.

        Returns:
            Matching life-history record.

        Raises:
            KeyError: If the organism has never been observed.
        """
        validated_id = validators.validate_int_ge(
            organism_id,
            bound=0,
            name="organism_id",
        )
        return self._histories[validated_id].snapshot()

    def parents_of(self, organism_id: int) -> tuple[int, ...]:
        """Return recorded biological parents for an organism.

        Args:
            organism_id: Permanent organism ID.

        Returns:
            Parent IDs, or an empty tuple when parentage is unknown.
        """
        return self.record(organism_id).parent_ids

    def offspring_of(self, organism_id: int) -> tuple[int, ...]:
        """Return recorded biological offspring for an organism.

        Args:
            organism_id: Permanent organism ID.

        Returns:
            Offspring IDs in birth order.
        """
        return self.record(organism_id).offspring_ids

    def should_observe(
        self,
        world_state: WorldState,
        *,
        step_index: int,
    ) -> bool:
        """Return whether the baseline population still needs registration."""
        _validate_state_observation_inputs(world_state, step_index=step_index)
        return not self._initialized

    def observe(
        self,
        world_state: WorldState,
        *,
        step_index: int,
    ) -> None:
        """Register the current population as the recorder's baseline cohort.

        Args:
            world_state: Authoritative world state at recorder attachment.
            step_index: Current simulation state index.

        Raises:
            RuntimeError: If a baseline has already been registered.
        """
        _validate_state_observation_inputs(world_state, step_index=step_index)
        if self._initialized:
            raise RuntimeError("PedigreeRecorder baseline has already been observed.")

        for organism in world_state.organisms.values():
            birth_step = _infer_birth_step(
                entry_step=step_index,
                entry_age=organism.age,
            )
            self._histories[organism.id] = _MutableLifeHistory(
                organism_id=organism.id,
                parent_ids=(),
                is_founder=True,
                entry_step=step_index,
                entry_age=organism.age,
                birth_step=birth_step,
            )

        self._initialized = True
        self._last_telemetry_step = step_index

    def should_observe_telemetry(self, telemetry: StepTelemetry) -> bool:
        """Return whether committed telemetry should update the pedigree."""
        _validate_step_telemetry(telemetry)
        return True

    def observe_telemetry(self, telemetry: StepTelemetry) -> None:
        """Update pedigree and life histories from one committed simulation step.

        Args:
            telemetry: Committed step telemetry in causal application order.

        Raises:
            RuntimeError: If the baseline state has not been observed first.
            ValueError: If telemetry is out of order or internally inconsistent.
        """
        _validate_step_telemetry(telemetry)
        if not self._initialized:
            raise RuntimeError(
                "PedigreeRecorder must observe a baseline WorldState before telemetry."
            )
        if (
            self._last_telemetry_step is not None
            and telemetry.completed_step_index <= self._last_telemetry_step
        ):
            raise ValueError(
                "PedigreeRecorder telemetry must have strictly increasing "
                "completed_step_index values."
            )

        for applied_event in telemetry.events:
            self._record_additions(
                applied_event,
                completed_step_index=telemetry.completed_step_index,
            )
            self._record_mortality(
                applied_event,
                completed_step_index=telemetry.completed_step_index,
            )

        self._last_telemetry_step = telemetry.completed_step_index

    def clear(self) -> None:
        """Remove all pedigree and life-history records."""
        self._histories.clear()
        self._initialized = False
        self._last_telemetry_step = None

    def _record_additions(
        self,
        applied_event: AppliedEvent,
        *,
        completed_step_index: int,
    ) -> None:
        added_ids = applied_event.added_organism_ids
        if not added_ids:
            return

        event = applied_event.event
        if isinstance(event, ParentageEvent):
            parent_ids = _validate_parent_ids(event.parent_ids)
        else:
            parent_ids = ()

        for organism_id in added_ids:
            if organism_id in self._histories:
                raise ValueError(
                    f"Organism {organism_id} entered pedigree history more than once."
                )

            if parent_ids:
                for parent_id in parent_ids:
                    if parent_id not in self._histories:
                        raise ValueError(
                            f"Parent {parent_id} is absent from pedigree history."
                        )

            self._histories[organism_id] = _MutableLifeHistory(
                organism_id=organism_id,
                parent_ids=parent_ids,
                is_founder=False,
                entry_step=completed_step_index,
                entry_age=0 if parent_ids else None,
                birth_step=completed_step_index if parent_ids else None,
            )

            for parent_id in parent_ids:
                self._histories[parent_id].offspring_ids.append(organism_id)

    def _record_mortality(
        self,
        applied_event: AppliedEvent,
        *,
        completed_step_index: int,
    ) -> None:
        event = applied_event.event
        if not isinstance(event, MortalityEvent):
            return

        deceased_ids = _validate_deceased_ids(event.deceased_organism_ids)
        removed_ids = frozenset(applied_event.removed_organism_ids)
        unremoved_ids = tuple(
            organism_id
            for organism_id in deceased_ids
            if organism_id not in removed_ids
        )
        if unremoved_ids:
            raise ValueError(
                "MortalityEvent deceased IDs must be removed by the same applied "
                f"event; not removed: {unremoved_ids!r}."
            )

        for organism_id in deceased_ids:
            try:
                history = self._histories[organism_id]
            except KeyError as error:
                raise ValueError(
                    f"Deceased organism {organism_id} is absent from pedigree history."
                ) from error

            if history.death_step is not None:
                raise ValueError(
                    f"Organism {organism_id} has more than one recorded death."
                )

            history.death_step = completed_step_index
            history.death_cause = applied_event.process_name
            history.death_process_type = applied_event.process_type


def _infer_birth_step(*, entry_step: int, entry_age: int) -> int | None:
    birth_step = entry_step - entry_age
    if birth_step < 0:
        return None
    return birth_step


def _validate_parent_ids(parent_ids: object) -> tuple[int, ...]:
    validated = validators.validate_tuple(parent_ids, name="parent_ids")
    if not validated:
        raise ValueError("ParentageEvent.parent_ids must not be empty.")
    _validate_unique_ids(validated, name="parent_ids")
    return validated


def _validate_deceased_ids(deceased_ids: object) -> tuple[int, ...]:
    validated = validators.validate_tuple(
        deceased_ids,
        name="deceased_organism_ids",
    )
    if not validated:
        raise ValueError("MortalityEvent.deceased_organism_ids must not be empty.")
    _validate_unique_ids(validated, name="deceased_organism_ids")
    return validated


def _validate_unique_ids(values: tuple[int, ...], *, name: str) -> None:
    seen: set[int] = set()
    for index, value in enumerate(values):
        validated_id = validators.validate_int_ge(
            value,
            bound=0,
            name=f"{name}[{index}]",
        )
        if validated_id in seen:
            raise ValueError(f"{name} must not contain duplicate ID {validated_id}.")
        seen.add(validated_id)


def _validate_optional_nonempty_string(
    value: str | None,
    *,
    name: str,
    required: bool,
) -> None:
    if value is None:
        if required:
            raise ValueError(f"{name} is required.")
        return
    validated = validators.validate_str(value, name=name)
    if not validated.strip():
        raise ValueError(f"{name} must not be empty or whitespace-only.")


def _validate_state_observation_inputs(
    world_state: WorldState,
    *,
    step_index: int,
) -> None:
    if not isinstance(world_state, WorldState):
        raise TypeError("world_state must be an instance of WorldState.")
    validators.validate_int_ge(step_index, bound=0, name="step_index")


def _validate_step_telemetry(telemetry: StepTelemetry) -> None:
    if not isinstance(telemetry, StepTelemetry):
        raise TypeError("telemetry must be an instance of StepTelemetry.")
