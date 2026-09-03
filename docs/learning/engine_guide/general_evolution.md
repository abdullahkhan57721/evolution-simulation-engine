# General Evolution: The Abstract Model

This chapter explains the project's evolution model **without assuming biology**.
That is essential because the architecture is deliberately broader than genomes,
organisms, sex, and heredity.

The authoritative concise companion is the
[General Evolution Framework](../../general_evolution_framework.md). This chapter
expands the same concepts pedagogically.

## Where you are in the architecture

```text
[KERNEL]
How are transitions executed?
        |
        v
[GENERAL EVOLUTION]  <-- YOU ARE HERE
What structure makes a changing system evolutionary?
        |
        v
[BIOLOGY]
How are those structures realized by organisms and genetics?
```

## Start with the broadest question: what is evolving?

A generic state-transition system can change through time without being
evolutionary. A counter that increments is changing, but we would not normally
call it evolution.

The project introduces additional semantics centered on **transmissible
information**.

At the broadest level used here:

> Evolution is change through time in the distribution or structure of
> transmissible information in a population or system.

That definition deliberately does not mention DNA, organisms, or reproduction.

## Evolving entities

An **entity** is a persistent unit chosen by the domain whose state can affect its
persistence, interactions, or contribution to future transmissible state.

Possible entities include:

```text
organism
cultural agent
software instance
strategy-bearing node
design lineage
artificial replicator
```

“Evolving entity” is a conceptual role, not a required universal base class.
Algorithms ask for narrow capabilities when they need them.

This is an important architecture lesson: the scientific category can be broader
than any one interface the code needs.

## Transmissible state

**Transmissible state** is information that can be copied, combined, modified, or
otherwise propagated to another recipient or future state.

It is the central general-evolution term in the repository.

Examples:

```text
biology              -> genome
information network  -> strategy token
cultural model       -> idea bundle
software evolution   -> parameter/program state
```

The generic capability is intentionally small:

```text
TransmissibleStateCarrier
    |
    +-- transmissible_state
```

That property says only:

> This object exposes information available to a propagation model.

It does not say the information is DNA, inherited vertically, or even sent to a
new entity.

## Transmission can have many directions

Biological parent-to-offspring inheritance is only one kind of transmission.
General propagation may be:

```text
vertical
    source -> new descendant

horizontal
    existing entity -> existing contemporary entity

oblique
    earlier/unrelated source -> recipient

replacement
    recipient keeps identity but changes carried state

multi-source
    several source states -> one resulting state
```

This is why the general layer uses **propagation** rather than treating
“inheritance” as the universal term.

## Expression: carried information is not necessarily operative behavior

An entity can carry information without acting directly on the raw representation.
A system may map transmissible state into **expressed state** or operative
characteristics:

```text
transmissible state
        |
        v
     expression
        |
        v
expressed / operative characteristics
```

The generic contract is `TransmissibleStateExpression`:

```text
express(transmissible_state) -> expressed value
```

### Nonbiological example

In the repository's information-network example:

```text
strategy token "amplify"
        |
        v
StrategyExpression
        |
        v
broadcast weight = 3
```

while:

```text
strategy token "retain"
        |
        v
StrategyExpression
        |
        v
broadcast weight = 1
```

The token and its operative effect are different things.

## Expression versus realization

Expression is not always the final story.

An operative characteristic may depend on:

```text
transmissible state
+
mutable current state
+
environment
+
history
+
stochastic development
```

That motivates a further conceptual distinction:

```text
transmissible information
        |
     expression
        |
encoded/expressed potential
        |
  context-dependent realization
        |
actual operative characteristic
```

This is especially important for biology, where genome, genetic phenotype,
developmental realization, environment, and current physiology should not be
collapsed into one object.

But the distinction is general. Learning, environmental history, or another
persistent non-transmissible influence can modify realized behavior in a
nonbiological model too.

## Propagation: construct a recipient transmissible state

The generic `PropagationModel` answers:

> Given zero or more source states, a recipient, immutable propagation context,
> and the simulation RNG, what transmissible state results for the recipient?

Conceptually:

```text
(source states, recipient, context, RNG)
                |
                v
          propagation model
                |
                v
         propagated state
```

The source count is deliberately unconstrained at the general level.

```text
0 sources  -> spontaneous/external construction is representable
1 source   -> copying/clonal/horizontal propagation
2 sources  -> biparental combination is representable
N sources  -> multi-source systems are representable
```

A specific domain policy may impose a stronger source-count rule.

That is the difference between **general contract** and **specialized policy**.

## Recipient is separate from sources

The recipient is an explicit, separate concept.

That matters because propagation need not create a new descendant. An existing
entity can receive a new transmissible state.

In the information-network example:

```text
source node
   |
   | strategy token
   v
TokenPropagation
   |
   v
existing recipient node receives replacement token
```

The recipient identity remains fixed while the composition of transmissible state
across the network changes.

That is genuine evolutionary change under the project's abstract model.

## Variation

**Variation** changes transmissible information during or between propagation
events.

The generic shape is:

```text
V(state, RNG) -> varied state
```

Variation can be:

- stochastic or deterministic;
- rare or frequent;
- independent by component or correlated;
- applied during propagation or as a separate modeled transition.

Biological mutation is a specialization of variation, not its definition.

### Variation does not have to happen every time

If a variation operator returns the same value most of the time, transmission can
still have enough fidelity for variants to persist while occasionally generating
new variants.

Evolution does not require a mutation on every step.

## Components and linkage

Transmissible state may contain smaller addressable components.

If those components propagate independently, modeling them separately is simple.
But often associations among components matter.

The general layer therefore includes linkage concepts:

```text
LinkageComponent
LinkageGroup
LinkagePosition
LinkageMap
```

### Linkage group

A **linkage group** identifies components that may remain associated during
transmission.

### Linkage position

A **linkage position** gives an ordering or coordinate inside that group.

### Linkage map

A **linkage map** describes how readily associations may be broken at different
positions/regions.

The abstraction is broader than chromosomes. A bundle of cultural practices or
features of a design could also be co-transmitted non-independently.

## Geometry versus breakpoint tendency

The framework separates two questions:

```text
Where are components located?
        |
        +--> linkage positions / geometry

How easily is association broken in each region?
        |
        +--> linkage map / local breakpoint intensity
```

This separation allows a uniform map or a piecewise map with sticky regions and
hotspots without redefining component geometry.

## Persistence and removal

Evolutionary entities can persist, transform, or leave the active system.

Removal may be caused by:

```text
intrinsic state
environment
competition
interaction
external rules
```

Biological death is one specialization, but general evolution needs only the
broader fact that entities can stop contributing to the active system.

Generic `departure` foundations therefore make sense independently of mortality.

## Entity production

Some evolutionary systems create new entities.

This raises a subtle but crucial distinction:

```text
PROPAGATION
What transmissible state should result?

PRODUCTION
How is an entity created from already-determined state/context?
```

These are not the same responsibility.

### Why separate propagation from production?

Transmission can happen without creating a new entity:

```text
existing node A
   |
   | token propagation
   v
existing node B changes token
```

And entity production can need information that is not part of transmissible
state propagation:

```text
placement
initial non-transmissible state
identity allocation
body mass
production environment
```

Combining propagation and production universally would make horizontal
transmission awkward and biological production too genetics-centric.

## Admission and departure are also separate

Producing an entity is not necessarily the same as inserting it into the active
domain state.

The generic foundations distinguish:

```text
production
    create entity

admission
    add entity to active modeled domain

departure
    remove entity from active modeled domain
```

Again, the goal is not class multiplication for its own sake. These responsibilities
have different semantics and may vary independently.

## Access and reference

Generic processes often need to:

```text
look up an entity
identify an entity stably
```

Those responsibilities are kept separate from the entity's biological meaning.
The general infrastructure therefore includes access/reference concepts rather
than assuming every domain uses the same container or integer-ID scheme.

## Interaction and competition

Evolution emerges in systems where entities and environments affect one another.
Candidate transitions may compete for:

```text
recipient
location
resource
partner
capacity
exclusive opportunity
```

The simulation kernel's resolver mechanism is useful here because it can make
competition explicit rather than allowing incidental execution order to decide.

Notice the layer interaction:

```text
[GENERAL EVOLUTION / DOMAIN]
defines what competition means

[KERNEL]
provides a generic resolution phase for competing proposed transitions
```

## Selection is usually emergent

One of the most important ideas in the model is that **selection does not need to
be a stored field**.

Suppose:

```text
variant A and variant B differ in transmissible state
        |
        v
that difference changes operative characteristics
        |
        v
those characteristics affect persistence or successful propagation
        |
        v
A contributes more often to future transmissible state than B
```

That differential contribution is selection.

The engine therefore does not require:

```python
entity.fitness = 0.83
```

A fitness statistic can be useful observationally, but the evolutionary mechanism
can arise from ordinary modeled transitions.

### Fitness versus selection

A **fitness measure** summarizes or estimates reproductive/persistence success
under some definition.

**Selection** is the population-level consequence when transmissible differences
are associated with differential future contribution.

Do not reverse the causal story by assuming an intrinsic scalar “fitness” must
exist before selection can happen.

## Darwinian evolution in the abstract

The project's general framework highlights a recurring combination:

1. **Variation** among entities or transmissible states.
2. **Differential persistence or propagation** associated with that variation.
3. **Sufficient transmission fidelity** for some differences to persist across
   propagation events.

That is enough to discuss Darwinian dynamics without requiring:

```text
genes
sex
fixed population size
mutation every step
explicit fitness field
vertical inheritance only
```

## The complete abstract loop

A useful master model is:

```text
                 transmissible state
                        |
          +-------------+-------------+
          |                           |
          v                           v
      variation                   expression
                                      |
                                      v
                          expressed characteristics
                                      |
                        + environment/state/history
                                      |
                                      v
                                 realization
                                      |
                                      v
                          operative characteristics
                                      |
                     +----------------+----------------+
                     |                                 |
                     v                                 v
               persistence                         interaction
                     |                                 |
                     |                           candidate transitions
                     |                                 |
                     +----------------+----------------+
                                      |
                                      v
                            successful propagation
                                      |
                                      v
                          future transmissible state
                                      |
                                      v
                         changed system composition
                                      |
                                      v
                                  EVOLUTION
```

Selection is not necessarily one extra box. It is the statistical pattern that
appears when some transmissible variants travel through this loop more
successfully than others.

## A concrete nonbiological proof

The repository's `examples/nonbiological_evolution.py` models persistent
information nodes.

```text
StrategyToken
    |
    v
StrategyExpression
    |
    v
broadcast weight
    |
    v
weighted chance of becoming propagation source
    |
    v
TokenPropagation + TokenVariation
    |
    v
recipient token replacement
    |
    v
changed token composition
```

Node identities and population size remain fixed. No organism is born and no
genome exists. Yet transmissible information changes composition because variants
differ in propagation influence and copying can vary.

This is why the nonbiological example is architecturally important: it tests the
meaning of the abstraction, not just import cleanliness.

## Abstraction ladder: from generic evolution to one run

```text
evolutionary system
    |
    v
transmissible-state propagation
    |
    v
one-source token replacement
    |
    v
TokenPropagation implementation
    |
    v
seed-84 information-network run
```

At each step downward, the model gains constraints and concrete meaning.

## Misconception checks

### “Transmissible state means genome.”

No. Genome is a biological realization of transmissible state.

### “Propagation means reproduction.”

No. Propagation can update an existing recipient without creating an entity.

### “Production means inheritance.”

No. Production creates an entity; inheritance/propagation determines
transmissible state.

### “An evolving entity must implement one universal interface.”

No. “Evolving entity” is a conceptual role; code asks for small capabilities as
needed.

### “Selection is a number stored on an entity.”

Not necessarily. Selection is typically an emergent differential contribution
pattern. Fitness numbers are measurements/models, not a prerequisite for the
mechanism.

### “Evolution requires sexual reproduction.”

No. Sexual reproduction is one biological propagation/production system.

## Design exercise: is this evolution?

Imagine twelve persistent software agents. Each carries a strategy string.
Every step, each agent copies a strategy from another agent. Strategies that make
agents more likely to be selected as sources spread more often. Copies sometimes
change one parameter.

Ask:

- What is the entity?
- What is the transmissible state?
- What is expression?
- What is variation?
- What is propagation?
- Is entity production required?
- Where would selection emerge?

If you can answer those without translating everything into organisms, you are
thinking at the intended abstraction level.

## You understand this chapter if you can…

- define transmissible state without using biological vocabulary;
- distinguish expression from context-dependent realization;
- explain why propagation accepts zero or more sources and a separate recipient;
- distinguish propagation, variation, production, admission, and departure;
- explain linkage without relying on chromosomes as the definition;
- describe selection as emergent differential contribution;
- identify evolutionary dynamics in the repository's persistent-node example; and
- map a new nonbiological evolutionary system onto the general concepts before
  thinking about kernel implementation.

Next: [Biological Specialization](biological_specialization.md).
