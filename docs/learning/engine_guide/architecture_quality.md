# Architecture Quality: More Than Correctness

Correct code can still be difficult to understand, expensive to change, badly
coupled, or poorly suited to future work. This page gives the quality vocabulary
used throughout the textbook so evaluations do not collapse into "good" or
"bad."

## The main lenses

```text
Correctness
    Does the implementation satisfy the intended behavior and invariants?

Semantic fidelity
    Does it preserve the modeled meaning, ordering, state visibility, and RNG rules?

Performance
    Does it scale appropriately, and what is actually expensive under measurement?

Readability
    Can another engineer reconstruct the algorithm and intent?

Maintainability
    Can behavior be changed safely without duplicating rules or touching unrelated code?

Extensibility
    Can real axes of variation be expressed behind stable contracts?

Testability
    Can important guarantees be verified independently and diagnostically?

Coupling
    How much does one component need to know about others?

Cohesion
    Do the responsibilities grouped together genuinely belong together?
```

No single score dominates every situation.

## Readability is analyzable

Instead of saying "this code is readable," inspect:

```text
control-flow locality
    Is the important algorithm visible in one place?

names
    Do names reveal domain/architectural meaning?

cognitive load
    How many simultaneous concepts must the reader hold?

branching/special cases
    How many alternate paths must be mentally simulated?

hidden dependencies
    Are state, configuration, randomness, and services explicit?

distance from cause to effect
    Is a decision separated from its consequence so far that intent disappears?

abstraction fit
    Do helpers/contracts correspond to real concepts or merely add indirection?
```

`StageCoordinator.coordinate()` is a useful positive example: despite private
dispatch/performance support, the semantic control flow remains visible as
proposal → resolution → preparation/materialization → application.

## Maintainability is future change cost

Ask:

```text
How many places encode this rule?
How many public contracts does the change cross?
Are there parallel implementations that must stay equivalent?
Are important dependencies explicit?
Do focused tests localize breakage?
Can a policy change without editing orchestration?
```

A representation with slightly more runtime overhead can be preferable if it keeps
one clear invariant boundary instead of creating multiple privileged construction
paths.

## Extensibility is not maximum genericity

Good extensibility means the design has an explicit place for **demonstrated axes
of variation**.

Bad extensibility often looks like speculative abstraction:

```text
Factory
  -> Registry
      -> Provider
          -> Adapter
              -> one implementation
```

when a simple function would do.

Ask:

> What real behavior needs to vary independently?

Examples in this project include resolver policy, biological inheritance policy,
variation models, and domain state shape. Pregnancy status is not a reason to add
a generic kernel lifecycle interface.

## Coupling and cohesion together

A highly cohesive component has responsibilities that naturally belong together.
A weakly coupled component does not need unnecessary knowledge about neighboring
layers.

`SequentialStepCoordinator` is cohesive around one responsibility: coordinate one
transactional step. It is weakly coupled to domain meaning because it depends on
stage behavior and `SimulationState`, not organisms or genomes.

## Testability is architecture feedback

If a behavior is hard to test without constructing half the application, ask
whether responsibilities are too entangled.

Useful focused boundaries include:

```text
copy semantics
stage simultaneity
resolver selection
materialization ordering
context lookup
preflight diagnostics
observation timing
```

Tests do not prove the architecture is ideal, but difficult test isolation can be
a useful smell.

## A balanced review

An implementation can be:

```text
fast but unreadable
readable but badly scaling
extensible but over-abstracted
maintainable but unnecessarily slow
simple but semantically incorrect
```

Engineering is not maximizing one axis. It is selecting a design whose tradeoffs
fit the problem and evidence.

## Overengineering check

Before adding an abstraction, ask:

```text
What current problem does it solve?
What variation does it isolate?
What duplicate logic does it remove?
What invariant does it make clearer?
What new concepts/paths does it add?
Could a smaller function or policy object solve the same problem?
```

If the justification is mostly "we might need this someday," wait for stronger
pressure.

## Performance and readability are not enemies by default

The best optimization often removes unnecessary work while preserving or improving
clarity:

```text
cache stable metadata once
avoid repeated conversion
choose a better data structure
reduce obviously duplicated work
```

The dangerous optimizations are those that create alternate semantic paths,
hidden invariants, or state/RNG behavior that is harder to reason about for a tiny
measured gain.

## You understand this page if you can...

- explain readability using concrete criteria rather than taste alone;
- distinguish maintainability from extensibility;
- identify speculative abstraction as a possible maintenance cost;
- use testability as one signal of responsibility separation; and
- explain why an engineering decision should balance correctness, performance,
  readability, maintainability, and evidence rather than maximize one metric.
