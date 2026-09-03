# Biological Evolution as a Specialization

The general evolution layer is intentionally broad. Biology gives those generic
relationships stronger, more specific meaning.

This chapter shows how the mapping works and why the biological layer should stay
biological rather than forcing biological vocabulary down into the kernel.

## Where you are in the architecture

```text
[KERNEL]
transition mechanics
        |
        v
[GENERAL EVOLUTION]
transmissible information and evolutionary relationships
        |
        v
[BIOLOGY]  <-- YOU ARE HERE
genomes, organisms, inheritance, development, reproduction, ecology
```

## The correspondence map

| General evolutionary concept | Biological specialization |
| --- | --- |
| evolving entity | organism |
| transmissible state | genome |
| transmissible component | allele-bearing locus/component |
| linkage group | chromosome |
| linkage position | locus position |
| expression | genetic architecture expressing a genome |
| expressed state | genetic phenotype |
| context-dependent realization | development / G×E / plasticity |
| operative characteristics | realized phenotype / physiology / behavior |
| propagation | biological inheritance |
| propagation source states | genomes of selected genetic contributors |
| variation | mutation and recombination |
| entity production | biological offspring production / birth |
| production-source entities | biology-defined production/placement context |
| admission | newborn enters active world state |
| departure | removal from active world state |
| persistence | survival |
| interaction | feeding, movement, predation, mating, competition |
| selection | differential survival and reproductive contribution |
| lineage | pedigree / genetic ancestry |

The mapping is directional:

```text
general concept
    -> stronger biological meaning
```

It is usually wrong to reverse it and define the general concept by the current
biology.

## Genome is transmissible state, but transmissible state is not “generic genome”

An `Organism` can expose its genome through the general
`transmissible_state` capability.

Conceptually:

```text
Organism
   |
   +-- biology-facing name: genome
   |
   +-- generic capability: transmissible_state
```

The biological API should still say `genome` where that richer meaning is known.
The general layer says `transmissible_state` because it must also support things
such as strategy tokens.

This is a general architecture principle:

> **Do not destroy useful domain vocabulary merely to make everything sound
> generic. Keep generic vocabulary at generic boundaries and precise vocabulary
> inside the specialization.**

## Genetic expression specializes transmissible-state expression

General evolution asks:

```text
transmissible state
        |
        v
     expression
        |
        v
expressed characteristics
```

Biology specializes that to:

```text
Genome
   |
   v
GeneticArchitecture / genetic expression
   |
   v
GeneticPhenotype
```

The general `TransmissibleStateExpression` contract deliberately makes the state
argument positional-only. A biological implementation can therefore present a
natural signature such as:

```text
express(genome)
```

without the general layer forcing the public parameter name
`transmissible_state` into biological code.

That is a small but instructive example of letting a structural contract preserve
semantics without controlling domain vocabulary.

## Genetic phenotype is not the whole phenotype

The architecture distinguishes several levels:

```text
Genome
  |
  v
genetic expression
  |
  v
GeneticPhenotype
  |
  + environment
  + developmental context/history
  + stochastic development
  |
  v
realized developmental phenotype / targets
  |
  + current physiology / reversible state
  |
  v
operative organism behavior/performance
```

Why preserve those distinctions?

Because biology contains different causal categories:

- inherited/transmissible information;
- expression of that information;
- developmental realization;
- environmental effects;
- transient physiological state;
- behavioral state.

If all of them become one mutable “phenotype” dictionary, it becomes difficult to
say what can be inherited, what is developmentally fixed, what is environmentally
responsive, and what can change minute-to-minute.

## Biological inheritance specializes propagation

The generic propagation contract is broader than reproduction:

```text
zero or more source states
recipient
immutable propagation context
RNG
        |
        v
   propagated state
```

Biological inheritance gives that shape stronger meanings:

```text
selected contributor genomes
recipient/offspring context
inheritance configuration
simulation RNG
        |
        v
   offspring genome
```

A concrete inheritance policy may impose source-count constraints.

For example:

```text
clonal inheritance
    requires exactly one source genome

current simple Mendelian sexual inheritance
    requires exactly two source genomes
```

Those are biological policy constraints, not universal restrictions on
`PropagationModel`.

## Mutation and recombination specialize variation

General variation says:

```text
state + RNG -> varied state
```

Biology supplies mechanisms such as:

```text
mutation
recombination
segregation-related variation
```

The general layer does not need to know what an allele is to provide a variation
contract.

Likewise, the kernel does not need to know that variation is occurring at all. It
only needs to coordinate whichever process/materialization consumes the simulation
RNG and later applies the result.

## Linkage becomes chromosomes and loci

General evolution separates:

```text
component
linkage group
position within group
local breakage/recombination tendency
```

Biology specializes those ideas:

```text
component      -> locus / allele-bearing unit
linkage group  -> chromosome
position       -> locus coordinate
breakage       -> recombination/crossover behavior
```

The generic abstraction is useful because “components tend to travel together” is
a transmissible-information relationship, not a fact unique to DNA.

## Persistence and departure become survival and death—but not only death

General departure means an entity leaves the active modeled system.

Biology may specialize departure into:

```text
mortality
migration/emigration
other removal
```

This distinction matters observationally. A world removal is not automatically a
death event.

Similarly, biological survival and mortality processes are domain rules above the
kernel. The kernel has no concept of being alive.

## Selection emerges through biology

Biological selection can arise because inherited differences change:

```text
survival
foraging success
predation risk
mate choice
reproductive eligibility
number of successful propagations
offspring survival
```

The engine does not need a universal intrinsic `fitness` field.

A lineage recorder may calculate lifetime reproductive contribution afterward,
but the selection mechanism is the differential result of modeled interactions.

This keeps the causal chain visible:

```text
genetic variation
   |
   v
expression / development
   |
   v
phenotypic differences
   |
   v
ecology / behavior / reproduction
   |
   v
differential persistence and genetic contribution
   |
   v
changed genotype/allele distribution
```

## Reproduction is where several relationships must be separated

Simple biology tempts us to collapse many roles into “parents.”

For a simple biparental organism, the same two individuals might:

```text
mate
consume reproductive energy
contribute genomes
determine offspring production context
appear in pedigree parentage
```

But those relationships are not logically identical.

The current architecture therefore distinguishes four biological sets.

## 1. Reproductive participants

**Reproductive participants** are the organisms involved in a reproductive
candidate and resolver-facing competition.

`ReproductiveGroup` records an ordered, nonempty set of unique participants.

Participants answer:

> Who is involved in this reproductive episode for mating/group formation and
> conflict/capacity semantics?

Resolver capacity remains participant-based.

## 2. Reproductive investors

**Reproductive investors** are the participant subset whose committed energetic
investment determines whether the reproductive proposal is affordable.

The policy role is `ReproductiveInvestorSelection`.

The default `AllParticipantsInvest` preserves the current simple case.

### Why investor selection occurs during proposal

Affordability determines whether the proposal should exist at all.

```text
candidate participant group
       |
       v
select investors
       |
       v
calculate required committed investment
       |
       v
affordable?
  |          |
 no         yes
  |          |
no proposal  proposal
```

The investor-selection contract intentionally has no RNG argument. If proposal-
time investor selection consumed randomness, candidates that are later rejected or
never become valid could disturb stochastic trajectories.

This is a beautiful example of **domain policy being placed according to kernel
transaction semantics**.

## 3. Genetic contributors

**Genetic contributors** are the participant subset whose genomes become source
states for biological inheritance.

The policy role is `GeneticContributorSelection`.

The default `AllParticipantsContribute` preserves simple clonal/biparental
configurations.

Contributor selection occurs during materialization, after the resolver has
accepted the reproductive candidate. Therefore rejected candidates do not consume
accepted-only contributor-selection randomness.

Only genetic contributors define genetic/pedigree parentage.

Conceptually:

```text
resolved reproductive participants
          |
   materialization
          |
          v
choose genetic contributors
          |
          v
extract contributor genomes
          |
          v
biological inheritance / propagation
          |
          v
offspring genome
```

## 4. Offspring-production sources

**Offspring-production sources** are the participant subset supplied through the
generic entity-production `source_entities` context.

The policy role is `OffspringProductionSourceSelection`.

The default `AllParticipantsAsProductionSources` preserves existing simple
behavior.

These sources can matter to biology such as:

```text
placement
newborn state
gestational/production context
other production-time policy
```

Production-source selection also occurs during materialization and may use the
simulation RNG.

## The four-way reproduction map

```text
                     reproductive participants
                              |
          +-------------------+-------------------+
          |                   |                   |
          v                   v                   v
     investors          genetic contributors   production sources
          |                   |                   |
          v                   v                   |
  committed energy       source genomes          |
                              |                   |
                              v                   |
                       inheritance /              |
                        propagation               |
                              |                   |
                              v                   |
                       offspring genome           |
                              |                   |
                              +---------+---------+
                                        |
                                        v
                         biological entity production
                                        |
                                        v
                                  world admission
```

Resolver conflicts remain about the full participant group. They are not silently
redefined according to whichever subset later invests, contributes genetics, or
supplies production context.

## Why this separation is not overengineering

The naive universal assumption is:

```text
participants
=
investors
=
genetic contributors
=
production sources
=
pedigree parents
```

That is a valid **policy** for many simple systems. It is a poor **universal
architecture rule**.

The current defaults deliberately recover the simple behavior:

```text
AllParticipantsInvest
AllParticipantsContribute
AllParticipantsAsProductionSources
```

So simple models remain simple while the public responsibilities stay honest.

## Thought experiment: three participants

Imagine a hypothetical reproductive event with participants `A`, `B`, and `C`.
The architecture can represent policies such as:

```text
participants:
    A, B, C

investors:
    B

genetic contributors:
    A, B

production sources:
    B, C
```

The point is not that the repository currently models a species with exactly this
biology. The point is that the architecture does not claim these relationships
must be identical when biology does not guarantee that.

Future systems involving external gestational hosts, caregivers, or resource
contributors may require even broader lifecycle semantics. The current selectors
choose subsets of resolved reproductive participants; expanding beyond that should
be an explicit future biological design decision rather than an implicit lookup of
arbitrary world entities.

## Mating type, reproductive role, and tuple position are different too

The biology layer also separates:

- **mating type** — an organism's reproductive identity;
- **reproductive role** — a contextual capability in a mating system;
- **tuple order** — meaningful only when a particular selector defines ordered
  roles.

That means the generic reproduction layer does not silently interpret
`participant_ids[0]` as a universal sex or role.

This keeps room for:

```text
multiple mating types
hermaphroditic systems
asymmetric roles
multi-participant groups
role-sensitive mate choice
```

without pushing those concepts into the kernel or general propagation contract.

## The current genetics frontier illustrates specialization discipline

The `Genome` representation can already hold arbitrary chromosome-copy
collections. The next biological front is not “make the kernel know ploidy.”

Instead, biology needs stronger policies for:

```text
expected copy counts
homolog pairing
segregation
gamete copy counts
recombination under those pairing rules
```

That is a useful test of architectural judgment:

> The data structure is already expressive enough; the missing semantics belong
> in the biological specialization, not in generic execution machinery.

## Vertical trace: inheritance through all layers

```text
[KERNEL]
Process / event / resolver / materialization / RNG / application
        |
        v
[GENERAL EVOLUTION]
TransmissibleStateCarrier / PropagationModel / VariationOperator
        |
        v
[BIOLOGY]
Organism.genome / contributor selection / inheritance / mutation / recombination
        |
        v
[REPRODUCTION ORCHESTRATION]
participant group
 -> proposal affordability/investors
 -> resolver
 -> contributor + production-source selection
 -> offspring genome
 -> offspring production
 -> admission
```

The same event therefore has several layers of explanation. The kernel explains
**when** phases happen. General evolution explains **what kind of information
relationship** is occurring. Biology explains **what that relationship means in
this domain**.

## Side-by-side: nonbiological propagation and inheritance

| Question | Information network | Biology |
| --- | --- | --- |
| Entity | `InformationNode` | `Organism` |
| Transmissible state | strategy token | genome |
| Expression | token -> broadcast weight | genome -> genetic phenotype |
| Sources | selected network node(s) | selected genetic contributor(s) |
| Recipient | existing node | offspring/biological recipient context |
| Propagation | copy token | inheritance |
| Variation | token flip | mutation/recombination |
| Production required? | no | normally yes for reproduction |
| Kernel phase for accepted-only stochastic detail | materialization | materialization |

This table is the strongest mental bridge between “abstract evolution” and
“biology built on it.”

## Misconception checks

### “If `Organism.genome` implements transmissible state, biology should rename the field.”

No. `genome` is the correct biological name. The generic capability provides an
additional abstraction boundary.

### “Inheritance is the general mechanism and propagation is a synonym.”

No. Propagation is broader. Inheritance is the biological specialization with
stronger lineage/genetic semantics.

### “All reproductive participants are parents.”

Not necessarily. Genetic parentage follows selected genetic contributors.

### “If an entity invests energy in reproduction, it must contribute genes.”

Not as a universal rule. Investment and genetic contribution are separate
responsibilities.

### “The offspring should be placed relative to its genetic parents.”

That may be the current simple policy, but production-source context is separate
so placement/production relationships are not forced to equal genetic parentage.

### “More biological detail belongs in the kernel because the kernel runs it.”

No. Execution mechanics belong in the kernel; modeled biological meaning belongs
above it.

## You understand this chapter if you can…

- map the general evolution concepts to biological genetics without defining the
  general concepts by biology;
- explain why genome, genetic phenotype, developmental realization, and current
  physiology are distinct layers;
- explain inheritance as a biological specialization of propagation;
- explain why ploidy/pairing/segregation are biological policy concerns rather
  than kernel concerns;
- distinguish reproductive participants, investors, genetic contributors, and
  production sources;
- explain why investor selection belongs at proposal time while contributor and
  production-source selection belong at materialization time; and
- trace one biological inheritance event from kernel mechanics through general
  propagation to biological reproduction.

Next: [Kernel Mental Model](kernel_mental_model.md).
