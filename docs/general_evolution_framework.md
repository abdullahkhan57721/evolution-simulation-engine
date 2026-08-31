# General Evolution Framework

The project is organized around three conceptually distinct layers:

```text
domain-neutral simulation kernel
        |
        v
general evolutionary semantics
        |
        v
biological specialization
```

The simulation kernel knows how to advance arbitrary transactional state through
ordered transition stages. It does **not** need to know what an organism, genome,
gene, phenotype, resource, or mating system is.

The general evolution layer describes the minimum semantics needed for systems
whose transmissible information can change in frequency or composition through
time. Biology then realizes those semantics with organisms, genomes, genetic
expression, development, reproduction, mutation, recombination, mortality, and
ecological interactions.

## 1. Domain-neutral simulation kernel

The kernel owns update mechanics rather than domain meaning:

```text
committed state
    |
    v
propose candidate transitions
    |
    v
resolve conflicts / competition
    |
    v
materialize accepted stochastic consequences
    |
    v
apply transitions to a working copy
    |
    v
commit completed step
    |
    v
observe
```

Its constitutional invariants are:

1. authoritative state is not mutated until a complete step succeeds;
2. RNG state is transactional with model state;
3. every stage proposes from one common stage-start state;
4. every accepted transition is materialized before any accepted transition in
   the stage is applied;
5. resolvers determine which competing proposals survive;
6. domain configuration is immutable shared context, not hidden mutable state;
7. static domain validation happens before execution;
8. runtime checks are reserved for facts that genuinely depend on evolving
   state.

This machinery can run a biological ecology, cultural evolution, competing
algorithms, technological lineages, artificial-life replicators, or even a
non-evolutionary discrete-event model.

## 2. Completely abstract evolutionary semantics

An evolutionary system needs more structure than a generic state-transition
system, but much less structure than biology.

### Evolving entities

An **entity** is a persistent unit whose state can affect its persistence,
interactions, or contribution to future transmissible state.

An entity need not be an organism. It could be a cultural agent, software
instance, strategy, design, molecule-like replicator, or another persistent
unit chosen by the modeled domain.

### Transmissible state

An entity may carry **transmissible state**: information that can be copied,
combined, modified, or otherwise propagated to another entity or future state.

This is the most general analogue of biological hereditary information.
Transmission need not be vertical parent-to-offspring inheritance. It can be:

- vertical transmission to newly created entities;
- horizontal transmission between contemporaneous entities;
- oblique transmission from unrelated earlier entities;
- copying with replacement;
- recombination of several source states;
- partial transfer of linked components.

### Expression

A system may map transmissible state into **expressed state** or **operative
characteristics** that affect interactions and transitions.

```text
transmissible state
        |
        v
expression
        |
        v
operative characteristics
```

Expression is optional. Some systems may act directly on transmissible state.

### Realization / context dependence

Operative characteristics may also depend on non-transmissible entity state,
environment, history, or stochastic development:

```text
transmissible state + mutable state + environment + history
                         |
                         v
                     realization
                         |
                         v
              operative characteristics
```

This distinction lets a system represent plasticity, learning, epigenetic-like
state, developmental noise, or other context-dependent realization without
pretending all operative state is transmitted.

### Propagation / transmission

A **transmission or propagation model** constructs a recipient transmissible
state from one or more source states and context.

Conceptually:

```text
T(source states, context, RNG) -> transmitted state
```

The recipient might be a new descendant, an existing entity being updated, or
another persistent carrier defined by the domain.

### Variation

**Variation** changes transmissible information during or between propagation
events.

```text
V(state, RNG) -> varied state
```

Variation may be stochastic or deterministic, local or global, independent by
component or correlated through linkage structure.

### Linkage and co-transmission

A transmissible state can contain addressable components whose propagation is
not independent.

A **linkage group** identifies components that can remain associated during
transmission. **Linkage position** gives an ordering or coordinate within that
group. A **linkage map** controls the local tendency for associations to be
broken.

This is intentionally more general than chromosomes and genes. In another
domain, nearby components of a design, strategy bundle, or cultural package
could exhibit correlated transmission.

### Persistence and removal

Entities may persist, transform, or leave the active population/system.
Removal may result from intrinsic state, interaction, resource competition,
environmental conditions, or externally imposed rules.

### Replication / entity production

Some evolutionary systems create new entities. Entity production is a state
transition that usually invokes transmissible-state propagation, but the two
concepts are not identical: transmission can occur without new entity creation.

### Interaction and competition

Entities and environmental structures can interact. Candidate transitions may
compete for mutually exclusive entities, locations, resources, recipients, or
other limited opportunities.

Resolvers represent this competition explicitly instead of hiding arbitrary
order dependence inside processes.

### Selection

**Selection is usually an emergent statistical consequence, not a stored field.**

Suppose variants of transmissible state affect operative characteristics, and
those characteristics influence persistence or successful propagation. Then
some transmissible variants contribute more to future system state than others.
That differential contribution is selection.

The engine therefore does not need an intrinsic scalar named ``fitness``.
Fitness measures can be observed after the fact or estimated from lineage and
propagation outcomes.

### Evolution

At the broadest level, evolution is change through time in the distribution or
structure of transmissible information in a population/system.

Darwinian evolution specifically requires a recurring combination of:

1. variation among entities or transmissible states;
2. persistence or propagation differences associated with that variation;
3. sufficient transmission fidelity for some of those differences to persist
   across propagation events.

Mutation is not required in every step; selection is not required to be
explicit; sexual reproduction is not required; genes are not required; and a
fixed population size is not required.

## 3. Biology as one specialization

Biological evolution maps naturally onto the abstract semantics:

| General evolutionary concept | Biological realization |
| --- | --- |
| evolving entity | organism |
| transmissible state | genome |
| transmissible component | allele-bearing locus |
| linkage group | chromosome |
| linkage position | locus position |
| expression | genetic architecture expressing a genome |
| expressed state | genetic phenotype |
| context-dependent realization | development / GxE / plasticity |
| operative characteristics | realized phenotype / physiology / behavior |
| propagation | biological inheritance |
| source entities | reproductive parents/contributors |
| variation | mutation and recombination |
| entity production | reproduction / birth |
| persistence/removal | survival, starvation, predation, age mortality |
| interactions | feeding, movement, predation, mating, competition |
| selection | differential survival and reproductive contribution |
| lineage | pedigree / ancestry |

Biological semantics therefore belong in a biological layer that configures the
general evolution and simulation machinery rather than inside the simulation
kernel itself.

## 4. Current general contracts

The `evo_engine.evolution` package already provides upstream contracts for:

- evolving entities carrying heritable/transmissible state;
- heritable-state expression;
- variation operators;
- transmission models;
- characteristic sources and requirements;
- linkage components, linkage groups, linkage positions, and linkage maps.

Some terminology still reflects the biological route by which these contracts
were first introduced, especially ``parent`` and ``descendant`` language in the
transmission API. The intended next abstraction step is to generalize this to
source/recipient propagation semantics while keeping biology-oriented adapters
such as ``InheritanceModel``.

## 5. Biological linkage as a special case

The standard genetics term for nearby genes tending to be inherited together is
**genetic linkage**. Recombination can separate linked loci, and the probability
of separation generally increases with distance between them.

The engine separates:

1. **geometry** — positions of transmissible components within a linkage group;
2. **local breakpoint intensity** — how permissive each region is to breaking
   that association.

`UniformLinkageMap` gives equal breakpoint intensity per coordinate.
`PiecewiseLinkageMap` supports relatively sticky regions and hotspots. A local
relative rate below one makes a region harder to break; zero prevents a
breakpoint there; a rate above one creates a hotspot.

Because the linkage API lives in the domain-neutral evolution layer, the same
machinery can model correlated transmission of nonbiological components.

## 6. Architectural dependency direction

The intended long-term dependency direction is:

```text
validation / generic telemetry primitives
        |
        v
simulation kernel
        |
        +-------------------+
        |                   |
        v                   v
general evolution      generic configuration contracts
        |                   |
        +---------+---------+
                  |
                  v
          biological specialization
                  |
                  v
       biological presets / experiments
                  |
                  v
             UI / files / API
```

The simulation kernel must not import modeled domains. The general evolution
layer must not import biological implementations. Biology may depend on both and
bind its concrete models into an immutable simulation context/specification.

The practical test for this boundary is simple: a nonbiological evolving system
must be runnable without constructing an ``Organism``, ``Genome``, ``WorldState``
with organisms, biological behavior policy, or ``GeneticArchitecture``.
