"""Complete reference ecological and evolutionary simulation preset."""

from evo_engine.presets.reference_ecology.builders import (
    ReferenceEcology,
    build_reference_engine,
    build_reference_simulation,
)
from evo_engine.presets.reference_ecology.config import (
    ReferenceEcologyConfig,
    ReferencePhysiologicalTradeoffs,
    ReferenceTraitValues,
)
from evo_engine.presets.reference_ecology.genetics import (
    build_reference_founder_genome,
    build_reference_genetic_architecture,
    build_reference_world,
)
from evo_engine.presets.reference_ecology.movement import (
    ReferenceExplorationMovement,
    ReferenceGaussianMovement,
    ReferenceMooreMovement,
    ReferenceUniformMovement,
    ReferenceVonNeumannMovement,
)
from evo_engine.presets.reference_ecology.observable import build_reference_ecology
from evo_engine.presets.reference_ecology.reproductive_investment import (
    ReferenceMatingTypeInvestmentScales,
    build_reference_reproductive_investment,
)
from evo_engine.presets.reference_ecology.spec import build_reference_spec

__all__ = [
    "ReferenceEcology",
    "ReferenceEcologyConfig",
    "ReferenceExplorationMovement",
    "ReferenceGaussianMovement",
    "ReferenceMatingTypeInvestmentScales",
    "ReferenceMooreMovement",
    "ReferencePhysiologicalTradeoffs",
    "ReferenceTraitValues",
    "ReferenceUniformMovement",
    "ReferenceVonNeumannMovement",
    "build_reference_ecology",
    "build_reference_engine",
    "build_reference_founder_genome",
    "build_reference_genetic_architecture",
    "build_reference_reproductive_investment",
    "build_reference_simulation",
    "build_reference_spec",
    "build_reference_world",
]
