from __future__ import annotations

from dataclasses import dataclass

from evo_engine.event import Event
from evo_engine.events_resolver import EventsResolver
from evo_engine.history import History
from evo_engine.observer import Observer
from evo_engine.state_updater import StateUpdater
from evo_engine.timestep_result import TimestepResult
from evo_engine.update_stage import UpdateStage

# Imports for type hints.
from evo_engine.world_state import WorldState


@dataclass
class TimestepCoordinator:
    update_stages: list[UpdateStage]
    events_resolver: EventsResolver
    state_updater: StateUpdater
    observer: Observer

    def coordinate(
        self,
        world_state: WorldState,
        history: History,
    ) -> TimestepResult:
        # Note to self (NTS): break the code below using private helper methods.

        working_state = world_state.copy()
        working_history = history.copy()

        for update_stage in self.update_stages:
            stage_proposed_events: list[Event] = []

            for events_proposer in update_stage.events_proposers:
                proposed_events: list[Event] = events_proposer.propose(
                    world_state=working_state,
                    history=working_history,
                )

                stage_proposed_events.extend(proposed_events)

            stage_resolved_events = self.events_resolver.resolve(
                proposed_events=stage_proposed_events,
                world_state=working_state,
                history=working_history,
            )

            working_state = self.state_updater.apply(
                events=stage_resolved_events,
                world_state=working_state,
            )

            if self.observer.should_observe(
                world_state=working_state,
                proposed_events=stage_proposed_events,
                resolved_events=stage_resolved_events,
                stage_name=update_stage.name,
            ):
                observation = self.observer.observe(
                    world_state=working_state,
                    proposed_events=stage_proposed_events,
                    resolved_events=stage_resolved_events,
                    stage_name=update_stage.name,
                )
                working_history.add(observation)

        working_state.advance_time()

        return TimestepResult(
            updated_world_state=working_state,
            updated_history=working_history,
        )
