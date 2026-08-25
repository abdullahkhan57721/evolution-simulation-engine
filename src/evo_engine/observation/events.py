"""Record committed event telemetry across a simulation run."""

from __future__ import annotations

import attrs

from evo_engine.telemetry import AppliedEvent, StepTelemetry
from evo_engine.validation import attrs_validators, validators


@attrs.define(slots=True, kw_only=True)
class EventRecorder:
    """Record immutable committed step telemetry over time.

    Attributes:
        every_n_steps: Positive completed-step observation interval.
    """

    every_n_steps: int = attrs.field(
        default=1,
        validator=attrs_validators.validate_int_ge(1),
    )
    _steps: list[StepTelemetry] = attrs.field(
        factory=list,
        init=False,
        repr=False,
    )

    @property
    def steps(self) -> tuple[StepTelemetry, ...]:
        """Return recorded step telemetry as an immutable tuple."""
        return tuple(self._steps)

    @property
    def events(self) -> tuple[AppliedEvent, ...]:
        """Return all recorded applied events in commit order."""
        return tuple(event for step in self._steps for event in step.events)

    @property
    def latest(self) -> StepTelemetry | None:
        """Return the latest recorded step telemetry, if any."""
        if not self._steps:
            return None
        return self._steps[-1]

    def should_observe_telemetry(self, telemetry: StepTelemetry) -> bool:
        """Return whether a committed step telemetry record should be stored.

        Args:
            telemetry: Committed step telemetry offered by the engine.

        Returns:
            ``True`` when the completed step falls on the configured interval
            and has not already been recorded.
        """
        _validate_telemetry(telemetry)
        if self._steps and self._steps[-1].completed_step_index == telemetry.completed_step_index:
            return False
        return telemetry.completed_step_index % self.every_n_steps == 0

    def observe_telemetry(self, telemetry: StepTelemetry) -> None:
        """Store one committed step telemetry record.

        Args:
            telemetry: Committed step telemetry to store.

        Raises:
            ValueError: If telemetry is supplied out of chronological order.
        """
        _validate_telemetry(telemetry)
        if self._steps and telemetry.completed_step_index <= self._steps[-1].completed_step_index:
            raise ValueError(
                "EventRecorder telemetry must have strictly increasing "
                "completed_step_index values."
            )
        self._steps.append(telemetry)

    def events_for_process(self, process_name: str) -> tuple[AppliedEvent, ...]:
        """Return all recorded events for one qualified or unqualified process.

        Args:
            process_name: Qualified or unqualified process class name.

        Returns:
            Matching applied events in commit order.
        """
        validated_name = validators.validate_str(process_name, name="process_name")
        if not validated_name.strip():
            raise ValueError("process_name must not be empty or whitespace-only.")
        return tuple(
            event
            for event in self.events
            if event.process_type == validated_name or event.process_name == validated_name
        )

    def clear(self) -> None:
        """Remove all recorded event telemetry."""
        self._steps.clear()


def _validate_telemetry(telemetry: StepTelemetry) -> None:
    if not isinstance(telemetry, StepTelemetry):
        raise TypeError("telemetry must be an instance of StepTelemetry.")
