"""Thin Qt controllers over existing Workbench application semantics."""

from evo_engine.desktop.controllers.application import ApplicationController
from evo_engine.desktop.controllers.evidence import EvidenceAuthoringController
from evo_engine.desktop.controllers.experiment import ExperimentAuthoringController
from evo_engine.desktop.controllers.presentation import PresentationController
from evo_engine.desktop.controllers.reference import ReferenceStudyController
from evo_engine.desktop.controllers.results import ResultsController
from evo_engine.desktop.controllers.run import RunController
from evo_engine.desktop.controllers.simulation import SimulationAuthoringController

__all__ = [
    "ApplicationController",
    "EvidenceAuthoringController",
    "ExperimentAuthoringController",
    "PresentationController",
    "ReferenceStudyController",
    "ResultsController",
    "RunController",
    "SimulationAuthoringController",
]
