"""General evolutionary-system abstractions."""

from evo_engine.evolution.characteristics import (
    CharacteristicRequirementProvider,
    CharacteristicSource,
    collect_required_characteristics,
    validate_required_characteristics,
)
from evo_engine.evolution.contracts import (
    TransmissibleStateExpression,
    VariationOperator,
)
from evo_engine.evolution.linkage import (
    LinkageComponent,
    LinkageMap,
    PiecewiseLinkageMap,
    RecombinationInterval,
    UniformLinkageMap,
    sample_linkage_breakpoint,
)

__all__ = [
    "CharacteristicRequirementProvider",
    "CharacteristicSource",
    "LinkageComponent",
    "LinkageMap",
    "PiecewiseLinkageMap",
    "RecombinationInterval",
    "TransmissibleStateExpression",
    "UniformLinkageMap",
    "VariationOperator",
    "collect_required_characteristics",
    "sample_linkage_breakpoint",
    "validate_required_characteristics",
]
