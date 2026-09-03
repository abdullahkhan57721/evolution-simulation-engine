# 0008 — Make chromosome-copy, pairing, and segregation semantics explicit

- **Status:** Accepted
- **Date:** 2026-09-03
- **Supersedes:** —
- **Superseded by:** —

## Context

`Genome` already stores arbitrary ordered chromosome copies, including multiple
copies sharing a chromosome name. The biological transmission path was less
general: `MeioticGameteFormation` grouped copies by chromosome name and selected
one transmitted copy per group, while recombination received the whole group and
therefore also had to confront pairing eligibility.

That made current simple Mendelian diploid behavior an implicit architectural
rule even though the underlying genome, gamete, inheritance, and expression
representations were more flexible.

## Decision

Keep chromosome-copy representation separate from biological copy semantics.

- `Genome` remains inherited chromosome-copy state/data.
- `Gamete` remains an ordered collection of transmitted chromosome copies and is
  not intrinsically haploid.
- `GeneticArchitecture` composes explicit chromosome-specific genome-structure
  expectations and validates them alongside existing locus/allele/expression
  requirements.
- Chromosome-copy expectations are chromosome-specific; there is no universal
  organism-level `ploidy` scalar in the core model.
- Homolog pairing is an explicit biological policy that creates transient
  chromosome associations.
- Recombination operates only on chromosome copies that pairing has already made
  eligible to interact; recombination does not choose partners.
- Recombination preserves the chromosome-copy cardinality of an association.
- Segregation is an explicit biological policy that decides which and how many
  recombination products enter a gamete.
- `MeioticGameteFormation` orchestrates pairing, recombination, and segregation
  rather than hard-coding one transmitted copy per chromosome name.
- The current simple policy continues to use chromosome-name equality for
  singleton/bivalent grouping. This is a property of that policy, not a permanent
  definition of all future homolog/homeolog relationships.
- A genome may be structurally valid for its `GeneticArchitecture` while being
  unsupported by a configured pairing/recombination/segregation policy.

## Alternatives considered

- **Global `GeneticArchitecture(ploidy=2)`.** Rejected because chromosome copy
  structure can vary by chromosome, organism/life-cycle state, or modeled system.
- **Put copy-count rules on `Genome`.** Rejected because `Genome` is inherited
  state while normal/allowed copy structure is model semantics.
- **Keep pairing inside recombination.** Rejected because partner selection and
  material exchange are independent responsibilities, especially once a group
  contains more than two copies.
- **Keep segregation inside one monolithic meiosis implementation.** Rejected
  because transmitted gamete copy count must be independently replaceable.
- **Introduce persistent homolog-group identifiers now.** Deferred because current
  requirements are satisfied by chromosome-type identity plus a pairing policy;
  stronger homeology/subgenome metadata should be added only when concrete biology
  requires it.

## Consequences

- Current diploid Mendelian behavior becomes one concrete policy composition
  rather than the universal genetic architecture.
- Mixed chromosome-copy structures can be validated without a global ploidy
  concept.
- Pairwise recombination can be reused by future higher-copy pairing policies that
  organize copies into bivalents.
- Richer polyploid pairing, multivalent recombination, nondisjunction, and
  chromosome-specific segregation remain future biological extensions.
- The frozen kernel, general propagation contracts, reproduction source-role
  architecture, development, and ecology are unchanged.

## References

- GitHub Issue #100
- `docs/development/current_state.md`
- `docs/development/roadmap.md`
- `docs/general_evolution_framework.md`
- `src/evo_engine/genetics/`
