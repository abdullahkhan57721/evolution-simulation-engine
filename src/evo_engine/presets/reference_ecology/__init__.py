"""Complete reference ecological and evolutionary simulation preset."""

from evo_engine.presets.reference_ecology.builders import (
    ReferenceEcology,
    build_reference_ecology,
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
from evo_engine.presets.reference_ecology.reproductive_investment import (
    ReferenceMatingTypeInvestmentScales,
    build_reference_parental_investment,
)

__all__ = [
    "ReferenceEcology",
    "ReferenceEcologyConfig",
    "ReferenceMatingTypeInvestmentScales",
    "ReferencePhysiologicalTradeoffs",
    "ReferenceTraitValues",
    "build_reference_ecology",
    "build_reference_engine",
    "build_reference_founder_genome",
    "build_reference_genetic_architecture",
    "build_reference_parental_investment",
    "build_reference_simulation",
    "build_reference_world",
]
