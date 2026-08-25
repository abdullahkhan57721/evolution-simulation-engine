# Allele and Genotype Frequencies

Population phenotype summaries do not fully describe evolutionary genetic state.
Distinct genotypes can express the same phenotype under dominance, and hidden
alleles can therefore change frequency without appearing in trait means.

`GeneticCompositionRecorder` observes inherited `Genome` state directly and
records raw allele-copy frequencies plus unphased genotype frequencies for
selected loci.

```python
from evo_engine.observation import GeneticCompositionRecorder

recorder = GeneticCompositionRecorder(
    locus_names=("growth_rate", "mating_signal"),
)

engine = SimulationEngine(
    step_coordinator=coordinator,
    stopping_condition=stopping_condition,
    observers=(recorder,),
)
```

## Allele frequencies

For each locus, `LocusComposition.alleles` records each observed raw allele
value, its copy count, and its frequency among all allele copies at that locus.
The recorder does not infer allele frequency from expressed phenotypes.

## Genotype frequencies

`LocusComposition.genotypes` records organism-level genotypes. Genotypes are
unphased for observation: reciprocal allele-copy order such as `(A, B)` and
`(B, A)` contributes to the same genotype count. This matches ordinary
genotype-frequency analysis while leaving chromosome-level phase in the
underlying `Genome` if a later analysis needs it.

The recorder does not assume diploidy. Genotypes retain however many allele
copies the organism's genome provides at the locus.

## Dominance example

Under complete dominance, both `A/A` and `A/a` may express phenotype `A`:

```text
phenotype observation
A/A -> A
A/a -> A

raw genetic observation
A/A -> genotype A/A
A/a -> genotype A/a
allele frequencies -> A: 75%, a: 25%
```

The phenotype and genetic-composition recorders therefore answer different
questions and should generally be used together.

## Reference ecology

The complete reference ecology attaches `GeneticCompositionRecorder`
automatically for every configured locus:

```python
from evo_engine.presets import build_reference_ecology

ecology = build_reference_ecology()
ecology.engine.run(ecology.simulation)

latest_genetics = ecology.genetic_recorder.latest
```

The full reference measurement stack is now:

```text
PopulationRecorder          -> expressed population state
EventRecorder               -> committed causal history
PedigreeRecorder            -> ancestry and individual fitness
GeneticCompositionRecorder  -> raw allele and genotype frequencies
```

All records are immutable observations. They do not retain mutable organism or
world references.
