# 0008 — Make chromosome transmission semantics explicit

- **Status:** Accepted
- **Date:** 2026-09-03
- **Supersedes:** —
- **Superseded by:** —

## Context

`Genome` already stores arbitrary ordered chromosome-copy collections, and genetic
expression can consume arbitrary allele-copy tuples. The biological transmission
path was less general: `MeioticGameteFormation` grouped chromosomes by name,
passed each complete group to recombination, and always transmitted exactly one
returned copy. `SingleCrossoverRecombination` consequently had to reject groups
larger than two because pairing and recombination responsibilities were conflated.

A global organism-level `ploidy` scalar would make ordinary diploidy convenient
but would poorly represent chromosome-specific copy counts, sex-chromosome
asymmetry, intentional aneuploid states, or future lifecycle-specific copy
regimes.

## Decision

Keep `Genome` as permissive inherited chromosome-copy data and make biological
structure and transmission policies explicit above it.

- `GenomeStructure`, composed by `GeneticArchitecture`, declares chromosome types
  and chromosome-specific allowed copy counts.
- `GeneticArchitecture.validate_genome()` owns structural genome validity in
  addition to existing locus, allele-domain, and expression validation.
- A structurally valid genome may still be unsupported by a configured
  transmission policy; those are different failure categories.
- `ChromosomePairingModel` organizes parent chromosome copies into temporary
  `ChromosomeAssociation` values.
- `RecombinationModel` receives an already-selected association. Recombination
  does not choose pairing partners and must preserve association copy cardinality.
- `ChromosomeSegregationModel` determines which and how many recombined chromosome
  copies enter a gamete.
- `MeioticGameteFormation` orchestrates pairing, recombination, and segregation
  rather than embedding one-copy-per-chromosome-name behavior.
- `SameNameBivalentPairing` and `BivalentSegregation` preserve current simple
  singleton/diploid Mendelian behavior as concrete policies.
- Chromosome-name equality is a convention of the current simple pairing and
  crossover policies, not a universal definition of biological homology.
- `Gamete`, `SexualInheritance`, general `PropagationModel`, and the frozen kernel
  remain copy-count-neutral or otherwise unchanged in responsibility.

## Alternatives considered

- **Add `GeneticArchitecture(ploidy=2)`.** Rejected because one global scalar
  prematurely makes a chromosome-independent copy number part of the architecture.
- **Put copy expectations only in gamete formation.** Rejected because structural
  genome validity should be meaningful outside one reproduction policy.
- **Store expected ploidy on `Genome`.** Rejected because the genome is modeled
  inherited state while expected structure is configuration/biological meaning.
- **Keep pairing inside recombination.** Rejected because partner selection and
  material exchange vary independently; the previous >2-copy crossover failure
  demonstrated the conflation.
- **Keep segregation implicit in `MeioticGameteFormation`.** Rejected because that
  would preserve one transmitted copy per chromosome name as universal behavior.
- **Introduce permanent homolog-group identity now.** Deferred because current
  requirements need temporary pairing associations, not another persistent
  chromosome identity axis. Future homeology or sex-chromosome evidence may
  justify richer structural metadata.

## Consequences

- Current diploid Mendelian behavior becomes an explicit composition rather than
  an architectural default hidden inside meiosis.
- Mixed chromosome-copy structures can be valid without a global ploidy number.
- A higher-copy genome can be structurally valid while the simple bivalent pairing
  policy explicitly reports that it cannot process it.
- Future polyploid pairing and segregation can be added as policies without
  replacing `Genome` or changing sexual inheritance source-count semantics.
- Richer recombination can build on explicit pairing associations instead of
  learning how to choose partners itself.
- Parent/somatic genome copy expectations remain distinct from the chromosome
  copies produced in a gamete.

## References

- GitHub Issue #102
- PR #103
- `src/evo_engine/genetics/genome_structure.py`
- `src/evo_engine/genetics/pairing.py`
- `src/evo_engine/genetics/recombination.py`
- `src/evo_engine/genetics/segregation.py`
- `src/evo_engine/genetics/gamete_formation.py`
- `tests/genetics/test_chromosome_transmission_semantics.py`
