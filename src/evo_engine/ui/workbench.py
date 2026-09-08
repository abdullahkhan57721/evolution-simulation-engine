"""Compatibility facade for Workbench world-presentation adapters.

Q0 moved the renderer-neutral adapter to :mod:`evo_engine.presentation.workbench`
so Streamlit and the native Qt frontend share one presentation contract.
"""

from evo_engine.presentation.workbench import (
    B3InteractiveArm,
    WorkbenchPresentationUnavailableError,
    WorkbenchWorldPresentation,
    build_b3_workbench_world_presentation,
    build_reference_workbench_world_presentation,
)

__all__ = [
    "B3InteractiveArm",
    "WorkbenchPresentationUnavailableError",
    "WorkbenchWorldPresentation",
    "build_b3_workbench_world_presentation",
    "build_reference_workbench_world_presentation",
]
