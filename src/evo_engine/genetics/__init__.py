"""Genetics domain models and policies."""

from evo_engine.evolution import (
    PiecewiseLinkageMap,
    RecombinationInterval,
    UniformLinkageMap,
)
from evo_engine.genetics.allele import Allele
from evo_engine.genetics.builtin_traits import (
    ADULT_BODY_MASS,
    ASSIMILATION_EFFICIENCY,
    ATTACK_STRENGTH,
    BUILTIN_TRAITS,
    CHOOSINESS,
    DEFENSE,
    DISEASE_RESISTANCE,
    ENDURANCE,
    ENERGY_CONSERVATION_THRESHOLD,
    ENERGY_RESERVE,
    GROWTH_RATE,
    LOCOMOTION_COST_COEFFICIENT,
    MATE_SEARCH_RANGE,
    MATING_SIGNAL,
    MATURITY_AGE,
    MAX_INTAKE_RATE,
    MAX_SPEED,
    MAXIMUM_AGE,
    METABOLIC_COST_COEFFICIENT,
    METABOLIC_EFFICIENCY,
    OFFSPRING_COUNT,
    OFFSPRING_ENERGY,
    REPRODUCTION_ENERGY_THRESHOLD,
    SENSORY_ACCURACY,
    SENSORY_RANGE,
    TEMPERATURE_OPTIMUM,
    TEMPERATURE_TOLERANCE,
)
from evo_engine.genetics.chromosome import Chromosome
from evo_engine.genetics.chromosome_association import ChromosomeAssociation
from evo_engine.genetics.domains import (
    AlleleDomain,
    ChoiceAlleleDomain,
    IntegerAlleleDomain,
)
from evo_engine.genetics.expression import (
    AdditiveIntegerExpression,
    CompleteDominanceExpression,
    ExpressionModel,
    MeanIntegerExpression,
)
from evo_engine.genetics.gamete import Gamete
from evo_engine.genetics.gamete_formation import (
    GameteFormation,
    MeioticGameteFormation,
)
from evo_engine.genetics.genetic_architecture import (
    GENETIC_ARCHITECTURE,
    GeneticArchitecture,
)
from evo_engine.genetics.genetic_phenotype import GeneticPhenotype
from evo_engine.genetics.genome import Genome
from evo_engine.genetics.genome_structure import (
    ChromosomeStructure,
    GenomeStructure,
)
from evo_engine.genetics.inheritance import (
    ClonalInheritance,
    InheritanceModel,
    SexualInheritance,
)
from evo_engine.genetics.locus import Locus
from evo_engine.genetics.mutation import (
    GaussianIntegerMutation,
    MutationPolicy,
    NoMutation,
    UniformChoiceMutation,
    UniformIntegerMutation,
)
from evo_engine.genetics.pairing import (
    ChromosomePairingModel,
    SameNameBivalentPairing,
)
from evo_engine.genetics.recombination import (
    NoRecombination,
    RecombinationModel,
    SingleCrossoverRecombination,
)
from evo_engine.genetics.requirements import (
    TraitRequirementProvider,
    collect_required_traits,
)
from evo_engine.genetics.segregation import (
    BivalentSegregation,
    ChromosomeSegregationModel,
)
from evo_engine.genetics.trait import Trait

__all__ = [
    "ADULT_BODY_MASS",
    "ASSIMILATION_EFFICIENCY",
    "ATTACK_STRENGTH",
    "BUILTIN_TRAITS",
    "CHOOSINESS",
    "DEFENSE",
    "DISEASE_RESISTANCE",
    "ENDURANCE",
    "ENERGY_CONSERVATION_THRESHOLD",
    "ENERGY_RESERVE",
    "GENETIC_ARCHITECTURE",
    "GROWTH_RATE",
    "LOCOMOTION_COST_COEFFICIENT",
    "MATE_SEARCH_RANGE",
    "MATING_SIGNAL",
    "MATURITY_AGE",
    "MAXIMUM_AGE",
    "MAX_INTAKE_RATE",
    "MAX_SPEED",
    "METABOLIC_COST_COEFFICIENT",
    "METABOLIC_EFFICIENCY",
    "OFFSPRING_COUNT",
    "OFFSPRING_ENERGY",
    "REPRODUCTION_ENERGY_THRESHOLD",
    "SENSORY_ACCURACY",
    "SENSORY_RANGE",
    "TEMPERATURE_OPTIMUM",
    "TEMPERATURE_TOLERANCE",
    "AdditiveIntegerExpression",
    "Allele",
    "AlleleDomain",
    "BivalentSegregation",
    "ChoiceAlleleDomain",
    "Chromosome",
    "ChromosomeAssociation",
    "ChromosomePairingModel",
    "ChromosomeSegregationModel",
    "ChromosomeStructure",
    "ClonalInheritance",
    "CompleteDominanceExpression",
    "ExpressionModel",
    "Gamete",
    "GameteFormation",
    "GaussianIntegerMutation",
    "GeneticArchitecture",
    "GeneticPhenotype",
    "Genome",
    "GenomeStructure",
    "InheritanceModel",
    "IntegerAlleleDomain",
    "Locus",
    "MeanIntegerExpression",
    "MeioticGameteFormation",
    "MutationPolicy",
    "NoMutation",
    "NoRecombination",
    "PiecewiseLinkageMap",
    "RecombinationInterval",
    "RecombinationModel",
    "SameNameBivalentPairing",
    "SexualInheritance",
    "SingleCrossoverRecombination",
    "Trait",
    "TraitRequirementProvider",
    "UniformChoiceMutation",
    "UniformIntegerMutation",
    "UniformLinkageMap",
    "collect_required_traits",
]
