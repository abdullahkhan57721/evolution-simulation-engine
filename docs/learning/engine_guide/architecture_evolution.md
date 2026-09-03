# How the Architecture Evolved

This is not a changelog. It is a **design narrative**: a selective account of the
problems that made the current abstractions necessary.

The goal is to prevent the final architecture from looking like complexity that
appeared all at once.

> Historical details here are pedagogical summaries. Git history, merged PRs,
> ADRs, current code, and tests remain authoritative for exact implementation
> history.

## Stage 1 — A biology-shaped simulation was the fastest way to learn the problem

Early development naturally centered the simulation directly on concepts such as:

```text
organisms
world state
aging
energy loss
death
reproduction
mutation
```

That was useful. A concrete vertical slice exposes requirements much faster than
trying to design a universal framework before any model runs.

A simple architecture can look like:

```text
WorldState
    |
    v
biological lifecycle rules
    |
    v
mutate organisms
```

### What this taught us

The project needed recurring mechanics for:

```text
candidate changes
ordered phases
conflicts
state updates
observation
reproducibility
```

### What eventually became limiting

When biological vocabulary lives inside execution machinery, today's biology can
silently become tomorrow's “generic” architecture.

Questions such as these become awkward:

```text
Could the scheduler run a nonbiological state?
Why should the kernel know an organism exists?
Why should generic state validation mention genomes or energy?
How will richer sexual reproduction fit if clonal assumptions are embedded low?
```

The lesson was not that starting concretely was a mistake. The lesson was that a
working concrete system had now revealed which mechanics were actually general.

## Stage 2 — Separate transition proposal from state mutation

As processes interact, direct sequential mutation creates hidden order dependence.

Naive form:

```text
process A mutates
process B sees A's mutation
process C sees A + B
```

That is correct only when the order is intended model causality.

The architecture moved toward explicit events and staged transition coordination:

```text
propose candidate transition
        |
        v
resolve conflicts
        |
        v
apply selected transition
```

### What problem this solved

It became possible to distinguish:

```text
what could happen
from
what is allowed to happen together
from
what actually mutates state
```

That separation is the ancestor of the current `Process` / `Resolver` /
`StageCoordinator` responsibilities.

## Stage 3 — Generalize the execution kernel away from biology

Once the orchestration mechanics were identifiable, the next question was:

> Which of these concepts genuinely belong to every simulation domain?

The answer was much smaller than the biological model.

The kernel was reshaped around:

```text
copyable domain state
simulation context
processes
events
resolvers
stages
steps
stopping conditions
observers
```

rather than organisms and lifecycle semantics.

This culminated in the explicit domain-neutral-kernel direction recorded in
[ADR 0001](../../decisions/0001-domain-neutral-kernel.md).

### The critical boundary

```text
SimulationState.domain_state
```

became an opaque modeled payload.

The kernel could now say:

> I know how to transact this state, but I do not know what it means.

That is the architectural move that makes `CounterState`, `InformationNetwork`,
and biological `WorldState` all legitimate payloads.

## Stage 4 — Separate immutable configuration from evolving state

A generic state object can become another dumping ground if every domain service
is added as a new mutable attribute.

The project separated:

```text
SimulationState
    mutable transactional run snapshot

SimulationContext
    immutable shared configuration/services
```

and introduced generic `SimulationSpec` compilation/preflight around the
configuration boundary.

### What problem this solved

- new domain services no longer expand the kernel state API;
- immutable configuration can be shared across transaction copies;
- generic dependency problems can fail before runtime;
- domain-specific compilers can add stronger validation above the generic layer.

This is why named context values today are **construction sugar**, not synthetic
state attributes.

## Stage 5 — Make state and randomness one transaction

A stochastic simulation is not reproducible if model state rolls back while its
random stream does not.

The kernel therefore made RNG ownership explicit inside `SimulationState`.

```text
transactional copy
    |
    +-- domain_state.copy()
    +-- clone complete RNG state
    `-- share immutable context
```

The rationale is recorded in
[ADR 0003](../../decisions/0003-transactional-state-and-rng.md).

### What problem this solved

A failed working step can consume randomness freely without changing the committed
trajectory, because the committed RNG object was never touched.

This also eliminated the need for hidden per-process random-generator ownership
rules.

## Stage 6 — Strengthen same-stage simultaneity with materialization

Proposal-before-application solves one order problem, but stochastic accepted
events reveal another.

Two bad alternatives are:

```text
materialize before resolution
    -> rejected candidates consume accepted-only RNG
```

and:

```text
materialize A
apply A
materialize B
    -> B sees A's same-stage mutation
```

The current stage contract became:

```text
propose all
-> resolve
-> materialize all accepted
-> apply accepted
```

This is documented in
[ADR 0002](../../decisions/0002-stage-simultaneity.md).

### What problem this solved

It preserves a useful simultaneity boundary while still allowing accepted events
to determine deferred stochastic consequences.

The important insight is that **materialization is a semantic phase**, not merely
an implementation hook.

## Stage 7 — Freeze the kernel and demand generic evidence for changes

Once the domain-neutral transaction semantics were coherent and protected by
focused tests, continued “generalization” could become harmful.

Every new biological feature creates tempting kernel conveniences. If accepted
casually, the kernel would gradually become biological again.

The project therefore documented and hardened the kernel as a stable maintenance
boundary in `docs/kernel_contract.md` and focused kernel-contract tests.

### New standard for a kernel change

A kernel change now needs evidence of something genuinely generic, such as:

```text
correctness deficiency
expressiveness deficiency
determinism/isolation defect
diagnostics problem
measured structural performance problem
```

“One biological feature would be easier this way” is not enough.

## Stage 8 — Build a general evolution layer above the kernel

A domain-neutral simulator is not automatically an evolution engine.

The next question was:

> What semantics are common to evolutionary systems without assuming biology?

The project separated concepts such as:

```text
transmissible state
expression
variation
linkage/co-transmission
propagation
production
admission/departure
access/reference
```

from biological genomes and reproduction.

This created a middle layer:

```text
kernel
    |
    v
general evolution
    |
    v
biology
```

### What problem this solved

Without the middle layer, there were only two options:

1. put evolution semantics in the kernel, making the kernel too specific; or
2. define all evolution in biological terms, making “general evolution” renamed
   biology.

The middle layer gives evolution its own domain-neutral vocabulary without making
all simulations evolutionary.

## Stage 9 — Prove the abstraction nonbiologically

An abstraction can look general on paper while still carrying hidden assumptions
from its original domain.

The strongest test was therefore not another diagram. It was an executable
nonbiological evolutionary system.

The information-network example uses:

```text
persistent nodes
strategy tokens
transmissible-state expression
weighted differential propagation
variation
recipient token replacement
```

with no biological organism, genome, reproduction implementation, or biological
world.

### What this proved

```text
kernel mechanics
+
general-evolution contracts
```

can produce genuine evolutionary change without biology.

That proof then exposed remaining generic terminology that was still too
biology-shaped.

## Stage 10 — Normalize vocabulary around transmissible state

The nonbiological proof made it clear that generic “heritable state” language was
stronger/narrower than the actual contracts.

The architecture standardized on **transmissible state** for the general layer and
removed the redundant universal evolving-entity carrier contract.

The rationale is recorded in
[ADR 0007 — Transmissible-state terminology](../../decisions/0007-transmissible-state-terminology.md).

### What problem this solved

The general layer now describes:

```text
vertical inheritance
horizontal transfer
replacement propagation
multi-source propagation
```

without pretending every transmission establishes biological-style heredity.

Biology keeps `genome` and `inheritance` because those stronger terms are correct
inside the specialization.

## Stage 11 — Audit biology as a specialization rather than redesigning the kernel

Once the generic layers were coherent, remaining architectural friction could be
examined where it actually lived: the biological specialization.

Reproduction exposed several assumptions that are true for simple current models
but not universal biological laws.

### Arity

Shared reproduction should not define one-parent or two-parent groups as universal.
Concrete inheritance policies may impose source-count requirements.

### Participation versus genetic contribution

Organisms participating in a reproductive episode are not logically identical to
organisms whose genomes contribute to offspring.

### Investment and production context

Participants are also not universally identical to:

```text
who pays energetic cost
who supplies gestational/placement/production context
```

The resulting current responsibilities are:

```text
reproductive participants
    |
    +-- proposal-time investors
    +-- materialization-time genetic contributors
    `-- materialization-time production sources
```

with simple all-participants defaults preserving current behavior.

### What this design sequence demonstrates

The response to richer biology was **not** to reopen the kernel.

Instead:

```text
stable generic execution
    |
    v
stable general evolution
    |
    v
richer biological policies
```

That is the architecture working as intended.

## Stage 12 — Current direction: deepen biology above stable lower layers

The current development front is explicit ploidy, homolog pairing, segregation,
and related recombination semantics.

The existing `Genome` container can already represent arbitrary chromosome-copy
collections. The missing work is about what those copies **mean biologically**.

That means the likely responsibilities are biological:

```text
expected copy counts
pairing
segregation
gamete copy counts
recombination under pairing rules
```

not new kernel concepts.

This is a useful final lesson from the history:

> Once boundaries are good, richer domain complexity should make the domain layer
> richer—not automatically make the infrastructure layer more complicated.

# The architecture as accumulated answers

The current engine can be summarized as a chain of questions and answers:

```text
How do we avoid hidden direct-mutation order dependence?
    -> proposal + explicit resolution

How do we preserve same-stage stochastic simultaneity?
    -> materialize all accepted before apply

How do we survive failed steps exactly?
    -> copy domain state + RNG transactionally

How do we avoid a biology-shaped scheduler?
    -> opaque domain_state + domain-neutral kernel

How do we supply fixed domain services without expanding state?
    -> immutable SimulationContext

How do we catch static wiring problems early?
    -> SimulationSpec preflight

How do we describe evolution without genes?
    -> transmissible-state general-evolution layer

How do we know that abstraction is real?
    -> nonbiological executable vertical slice

How do we support richer reproduction?
    -> specialize biology with independent responsibilities,
       not new kernel assumptions
```

# How to use history when designing new features

Do not argue:

> “The architecture has always done X, so X must remain.”

History is useful for recovering **which problem a boundary solves**.

A better design question is:

> “Does the original failure mode still matter, and does this proposed change
> preserve or deliberately replace the invariant that solved it?”

That is why ADRs and focused tests are more useful than folklore.

# You understand this chapter if you can…

- explain why the project could reasonably start biology-shaped and still need a
  domain-neutral kernel later;
- identify the failure mode that motivated proposal/resolution separation;
- explain why RNG had to become part of transactional state;
- derive materialization from rejected-event RNG and same-stage visibility
  problems;
- explain why the nonbiological vertical slice was stronger evidence than naming
  generic Protocols;
- explain why reproduction hardening happened in biology rather than the frozen
  kernel; and
- use project history to recover design rationale without treating old
  implementation details as permanent requirements.

Return to [Kernel Design Rationale and Invariants](kernel_design_rationale.md) to
connect this history to the current protected contracts.
