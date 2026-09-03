# Architectural Roadmap

This page answers **where the project is going** at the level of coherent
architectural milestones. It is a rolling planning aid, not an implementation
ticket system.

## Authority and maintenance boundary

GitHub Issues remain authoritative for the scope, acceptance criteria, status,
and dependencies of active implementation work. Architecture/subsystem docs and
ADRs remain authoritative for settled contracts and rationale.

This roadmap should change when milestone ordering or architectural direction
materially changes. It should not mirror every Issue, PR, commit, or transient
status update.

## Guiding direction

The project is moving toward a simulation engine in which:

1. the frozen kernel provides domain-neutral deterministic transactional
   execution;
2. the general evolution layer expresses evolution without assuming biology;
3. biological genetics, reproduction, development, and ecology specialize those
   settled general contracts;
4. richer modeled biology is added only after the abstraction boundary it depends
   on is coherent;
5. experiments, observation, and interfaces expose the resulting model without
   pushing domain assumptions back into lower layers.

The kernel is not the current development frontier. New modeled behavior normally
belongs above it unless a genuine generic deficiency is demonstrated.

For the v0.1 portfolio release, the immediate priority is to **demonstrate the
architecture already present** rather than broaden biology. The reference ecology,
committed observation stack, experiment API, checkpointing, and export system are
stable enough to support a polished interactive presentation layer above them.

## Near-term dependency graph

```text
#84 / #85
nonbiological evolutionary vertical slice
        |
        v
#86
transmissible-state contract normalization
        |
        v
#92 → #95 → #98/#99
reproduction boundary hardening
        |
        v
#102 / #103
chromosome-copy / pairing /
segregation foundation
        |
        v
#106 / #107
committed spatial observation boundary
        |
        v
#108 / #109
portfolio reference-ecology dashboard
        |
        v
M2 adaptive curated configuration
        |
        v
M3 renderer-neutral cinematic proof
        |
        v
M4 flagship evolutionary demonstration
        |
        v
M5 v0.1 release hardening / verification
        |
        +-----------------------+-----------------------+
        |                       |                       |
        v                       v                       v
richer genetics          richer mating systems    richer development /
                                                  evolutionary ecology
```

A future native execution backend is a separate evidence-driven architectural
front after the portfolio release. Near-term UI work should preserve static typed
configuration and committed result boundaries that would make such a backend
possible without redesigning the kernel or `SimulationSpec` speculatively.

Richer genetic-expression and development/G×E models remain valid post-v0.1
fronts once their own public responsibilities are clear; they do not block the
portfolio release.

## Portfolio release front — Interactive reference ecology

**Status:** committed spatial presentation boundary completed by Issue #106 /
PR #107; dashboard implemented by Issue #108 / PR #109. Adaptive configuration is
the next presentation capability, followed by a downstream cinematic-rendering
proof, a flagship demonstration, and final v0.1 hardening.

**Goal:** expose the strength of the existing engine through a polished,
reproducible end-to-end experience without creating a second simulation
architecture.

The settled presentation direction is:

```text
simulation/domain layers
        |
        v
committed observation / experiment values
        |
        +-----------------------+
        |                       |
        v                       v
interactive presentation   cinematic presentation
(Streamlit / Plotly)       (future Manim)
```

Renderers remain downstream consumers. Committed observation/result values should
not contain Plotly, Streamlit, Manim, animation-frame, or other renderer-owned
concepts. Do not introduce a generic replay framework unless implementation finds
a concrete reusable-data gap that forces renderer-specific assumptions into
committed simulation results.

`SpatialRecorder` supplies the opt-in immutable spatial history needed for world
playback. The Streamlit/Plotly dashboard consumes that boundary plus the existing
population, genetic-composition, event, pedigree/life-history, experiment, and
export contracts. It retains completed immutable presentation values rather than
mutable worlds or engines.

Curated configuration should evolve through real supported model choices rather
than a dump of every internal field. Conditional visibility belongs to the UI,
while selected values must normalize into actual typed configuration before the
engine runs. Hidden or stale UI state must never become implicit simulation
configuration, and adding adaptive forms does not authorize fabricating model
modes the preset does not support.

The remaining v0.1 presentation sequence is deliberately narrow:

1. **M2 — adaptive curated configuration:** prove conditional configuration using
   supported reference-ecology controls while preserving typed validation and an
   explicit run action;
2. **M3 — renderer-neutral cinematic proof:** consume existing committed values
   from a downstream Manim renderer without making the renderer a simulation
   owner or introducing speculative replay architecture;
3. **M4 — flagship evolutionary demonstration:** compose existing simulation,
   observation, interactive, and cinematic capabilities into one reproducible
   portfolio story rather than broadening biology merely for visual drama;
4. **M5 — v0.1 release hardening:** perform browser-level visual QA,
   deployment/discoverability work, README/media polish, release tagging, and
   final reproducibility/CI verification.

The v0.1 release should prioritize:

- adaptive but curated reference-ecology configuration and understandable
  validation errors;
- committed spatial playback;
- population/ecological, heritable-trait, genetic, event, and life-history views;
- reproducible multi-seed experiment comparison;
- existing JSON/CSV exports;
- renderer-neutral committed evidence reusable by interactive and cinematic
  presentation;
- concise portfolio-oriented README/release instructions;
- reliable headless UI and full protected-CI verification;
- deployment/discoverability polish only where it materially improves portfolio
  presentation.

**Non-goals before v0.1:** richer recombination, richer mating systems, new
biology subsystems, kernel redesign, live mutable-engine browser ownership,
checkpoint upload/resume UI, databases, a custom frontend/backend stack, native
Rust/C++ execution, or speculative `SimulationReplay`/backend-neutral-plan
frameworks.

After v0.1, the modeled-domain milestones below resume against their settled
contracts. Any native-backend milestone should begin from measured requirements
and preserve the distinction between Python modeling/configuration, a possible
future static compiled plan, backend execution, and committed result values.

## Milestone 1 — General-evolution contract normalization

**Status:** completed by Issue #86.

**Goal:** reconcile the biology-shaped `EvolutionaryEntity` /
`HeritableStateExpression` / `heritable_state` vocabulary with the broader
`TransmissibleStateCarrier` / `transmissible_state` model demonstrated by the
nonbiological vertical slice.

The settled contract uses `transmissible state` as the canonical generic term,
renames expression to `TransmissibleStateExpression`, and removes the redundant
`EvolutionaryEntity` carrier Protocol without compatibility aliases. Biological
inheritance and genome terminology remain domain-native specializations. See ADR
0007 for the rationale.

**Constraints preserved:**

- source/recipient propagation semantics;
- the frozen kernel;
- production/lifecycle/genetics behavior and package boundaries;
- one coherent pre-1.0 migration without compatibility aliases.

## Milestone 2 — Harden biological reproduction boundaries

**Status:** completed through Issues #92, #95, and #98.

**Goal:** make biological reproduction a clean specialization of general
propagation and entity production without treating the simplest current mating
systems as universal architecture.

The resulting conceptual path is:

```text
eligible organisms
        |
        v
reproductive participants
        |
        +----------------------+----------------------+
        |                      |                      |
        v                      v                      v
reproductive investors  genetic contributors  production-source context
        |                      |                      |
        v                      v                      |
committed energy          source genomes             |
                               |                      |
                               v                      |
                      inheritance / propagation       |
                               |                      |
                               v                      |
                        offspring genome              |
                               |                      |
                               +----------+-----------+
                                          |
                                          v
                              expression + development
                                          |
                                          v
                              biological offspring production
                                          |
                                          v
                                   world admission
```

Issue #92 established that shared reproductive groups may contain any nonempty
ordered tuple of unique participants and that source-count requirements belong to
concrete inheritance models. Clonal inheritance remains a one-source policy and
the current Mendelian sexual model remains a two-source policy.

Issue #95 established **reproductive participation** and **genetic contribution**
as separate responsibilities. Resolver-facing groups contain participants;
`GeneticContributorSelection` chooses the ordered contributor subset only during
materialization, preserving transaction/RNG semantics. Existing simple
configurations use `AllParticipantsContribute`, while pedigree `parent_ids`
unambiguously mean genetic/transmissible-state contributors.

Issue #98 completed the critical source-role hardening by separating
**reproductive investors** and **offspring-production sources** from both the
participant and genetic-contributor sets. `ReproductiveInvestorSelection` runs
while proposals are formed because affordability determines proposal existence;
its default `AllParticipantsInvest` preserves current behavior and its contract
intentionally exposes no RNG argument. `OffspringProductionSourceSelection` runs
only during materialization and may use the simulation-owned RNG; its default
`AllParticipantsAsProductionSources` preserves current production/placement
behavior. Resolver conflicts continue to use all participants, while materialized
events retain genetic parentage separately from production-source identity.

These shared selectors currently choose subsets of the resolved reproductive
participants. Future biology involving external gestational hosts, caregivers, or
energy/resource contributors should broaden that boundary only with explicit
lifecycle and conflict semantics rather than by silently reaching into arbitrary
world entities.

**Constraints preserved:**

- no kernel change unless a genuine generic deficiency is demonstrated;
- no redesign of `Genome` merely to support variable contributor count;
- preserve materialize-before-apply and simulation-owned RNG semantics;
- preserve simple clonal and biparental configurations as concrete policies.

**Implementation mode:** ChatGPT for public contracts and representative
implementation; Codex only for broad mechanical migration after contracts settle.

## Milestone 3 — Richer genetic expression

**Goal:** extend the existing copy-count-aware, multi-locus expression framework
with additional biological expression policies rather than redesigning general
evolution.

The current architecture already supports multi-locus expression and complete
dominance. Future models can add, as evidence and use cases require:

- incomplete dominance;
- codominance;
- epistasis and other locus interactions;
- dosage-sensitive expression;
- richer quantitative architectures.

The important boundary remains:

```text
genome
  |
  v
genetic expression
  |
  v
genetic phenotype
  |
  v
development / environment-dependent realization
```

Expression extensions should not collapse genetic phenotype, developmental
realization, and current mutable physiological/behavioral state into one catch-all
object.

**Implementation mode:** ChatGPT for new public-model semantics; settled,
independent expression policies and test matrices are good Codex candidates.

## Milestone 4 — Explicit chromosome-copy, pairing, segregation, and recombination foundations

**Status:** foundational responsibility split completed by Issue #102 / PR #103.

**Goal:** deepen biological transmission without narrowing general propagation or
making ordinary diploidy universal architecture.

`Genome` remains permissive inherited chromosome-copy data. Biological structural
meaning is now explicit above it:

```text
Genome
  |
  v
GenomeStructure + GeneticArchitecture validation
  |
  v
ChromosomePairingModel
  |
  v
ChromosomeAssociation(s)
  |
  v
RecombinationModel
  |
  v
ChromosomeSegregationModel
  |
  v
Gamete
```

`GenomeStructure` declares chromosome types and chromosome-specific allowed copy
counts; there is no foundational organism-wide `ploidy` scalar. A structurally
valid genome may still be unsupported by a configured transmission policy.

Pairing now decides temporary chromosome associations before recombination.
Recombination operates only within those supplied associations and preserves copy
cardinality. Segregation separately determines which and how many chromosome
copies enter a gamete. `MeioticGameteFormation` composes those policies rather
than embedding a universal one-copy-per-chromosome-name rule.

`SameNameBivalentPairing`, `NoRecombination` /
`SingleCrossoverRecombination`, and `BivalentSegregation` preserve current simple
singleton/diploid Mendelian behavior. Chromosome-name equality is therefore a
convention of the current simple policies, not a permanent definition of
homology.

A representative higher-copy test proves that a four-copy chromosome group can
be structurally valid, be organized by an explicit alternative pairing policy
into two bivalents, form a two-copy gamete through ordinary bivalent segregation,
and flow through existing `SexualInheritance` to a valid four-copy offspring.
That proof establishes architectural extensibility without shipping a production
polyploid meiosis model prematurely.

### Remaining genetics direction

Build richer behavior on these settled contracts only when a concrete biological
use case justifies it. Candidate follow-ups include:

- production higher-copy pairing policies, including random or preferential
  bivalents and eventually multivalents;
- chromosome-specific pairing behavior;
- chromosome-specific and multiple-crossover recombination;
- role-, mating-type-, or lifecycle-sensitive gamete formation where required;
- more explicit sex-chromosome or homeolog semantics if same-name grouping is no
  longer sufficient.

Do not add these capabilities merely to enumerate biological possibilities. The
next genetics milestone should choose a concrete richer recombination/pairing case
that exercises the new responsibility boundary.

This remains a biological specialization. General `PropagationModel` and the
frozen kernel do not need chromosome-copy, homolog, meiosis, or segregation
concepts.

**Implementation mode:** ChatGPT for new pairing/recombination semantics and public
contracts; Codex selectively for settled repetitive test matrices or mechanical
migrations.

## Milestone 5 — Richer mating systems

**Status:** architecturally unblocked and may advance alongside the genetics front.

**Goal:** extend the existing mating-type and reproductive-role infrastructure
beyond primarily pairwise group formation.

The project already supports arbitrary mating-type labels, compatibility networks,
multiple reproductive roles per mating type, arity-neutral reproductive groups,
contributor subsets distinct from participants, independent investor subsets, and
independent offspring-production source subsets. Future work should build on those
capabilities toward:

- asymmetric and ordered roles;
- multi-participant reproductive groups;
- hermaphroditic systems;
- role-sensitive mate choice;
- richer policies determining which participants contribute genetic state or
  reproductive investment.

Mating-system composition should remain separate from low-level inheritance.

## Milestone 6 — Richer development and phenotype realization

**Goal:** extend the existing environmental and G×E developmental realization
path while preserving clear distinctions among inheritance, genetic expression,
development, environment, and current physiological/behavioral state.

Potential fronts include:

- nonlinear reaction norms;
- developmental timing and stages;
- environmental history;
- richer developmental stochasticity;
- explicit reversible adult plasticity distinct from lifetime developmental
  targets.

The existing frozen `DevelopmentalProfile` should not become a catch-all mutable
phenotype merely to accommodate dynamic plasticity.

## Milestone 7 — Richer evolutionary ecology

**Goal:** use the stable biological boundaries to model more consequential
selection pressures and interactions without pushing ecological meaning into
general evolution or the kernel.

Possible fronts include richer resource competition, movement/behavior,
predation, life-history tradeoffs, environment-dependent reproductive outcomes,
and biogeographic structure. Selection should continue to emerge from
differential persistence and propagation rather than becoming an intrinsic
generic scalar field.

Critical reproduction-boundary and chromosome-transmission-foundation hardening
are complete. Major ecology work does not need to wait for every future expression,
recombination, mating, or development feature; add those capabilities when
concrete ecological or biological use cases require them.

## Cross-cutting fronts

The following concerns continue alongside modeled-domain milestones when there is
concrete need:

- observation and analysis of evolutionary outcomes;
- reproducible experiment composition and export;
- checkpoint/resume guarantees;
- documentation and examples;
- performance measurement based on evidence;
- portfolio UI/release polish above stable production contracts.

Do not turn these into foundational redesigns merely because they are
cross-cutting.

## ChatGPT versus Codex allocation

Use ChatGPT Chat primarily when work is:

- architecture-heavy;
- a consequential public-contract decision;
- tightly scoped and sequential;
- easier because the design conversation itself is important context;
- an independent architectural review.

Use Codex selectively when work is:

- execution-heavy behind settled contracts;
- broad and repetitive;
- a mechanical migration across many files;
- validation/debug-cycle intensive;
- independently parallelizable;
- valuable to run unattended while other design work continues.

Optimize for total time and attention required to reach a correct merged change,
not for a blanket preference for one implementation agent.

## Planning rule

Before opening each new milestone Issue:

1. re-read current `main` and `docs/development/current_state.md`;
2. verify whether earlier milestones changed the assumptions in this roadmap;
3. settle consequential architecture in Chat before implementation when needed;
4. create a focused Issue with explicit dependencies, boundaries, non-goals,
   acceptance criteria, and verification;
5. update this roadmap in the same PR when the milestone materially changes
   ordering or architectural direction.

A roadmap is a hypothesis about the best sequence. Evidence from implementation
may change it.
