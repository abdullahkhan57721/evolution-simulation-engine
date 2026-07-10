from __future__ import annotations

from evo_engine.events_proposer import AgingEventsProposer
from evo_engine.events_resolver import EventsResolver
from evo_engine.history import History
from evo_engine.observer import Observer
from evo_engine.organism import Organism
from evo_engine.simulation_engine import SimulationEngine
from evo_engine.state_updater import StateUpdater
from evo_engine.stopping_condition import StoppingCondition
from evo_engine.timestep_coordinator import TimestepCoordinator
from evo_engine.update_stage import UpdateStage
from evo_engine.world_state import WorldState


def build_basic_aging_engine(
    initial_population: int, max_time_steps: int
) -> SimulationEngine:

    # Create organisms
    organisms = []

    for organism_id in range(initial_population):
        organisms.append(Organism(id=organism_id))

    # Create initial world state
    initial_world_state = WorldState(time_step=0, organisms=organisms)

    # Initialize History
    initial_history = History(observations=[])

    # Initialize AgingEventsProposer
    aging_events_proposer = AgingEventsProposer()

    # Create the aging update stage
    aging_stage = UpdateStage(
        name="aging",
        events_proposers=[aging_events_proposer],
    )

    # Creating the list of update stages in order of application
    update_stages = [aging_stage]

    # Initialize EventsResolver
    events_resolver = EventsResolver()

    # Initialize StateUpdater
    state_updater = StateUpdater()

    # Initialize Observer
    observer = Observer()

    # Create TimestepCoordinator
    timestep_coordinator = TimestepCoordinator(
        update_stages=update_stages,
        events_resolver=events_resolver,
        state_updater=state_updater,
        observer=observer,
    )

    # Create StoppingCondition
    stopping_condition = StoppingCondition(max_time_steps=max_time_steps)

    # Create SimulationEngine
    simulation_engine = SimulationEngine(
        world_state=initial_world_state,
        stopping_condition=stopping_condition,
        timestep_coordinator=timestep_coordinator,
        history=initial_history,
    )

    return simulation_engine
