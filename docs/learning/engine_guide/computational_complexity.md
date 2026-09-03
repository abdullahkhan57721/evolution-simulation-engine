# Computational Complexity and Performance Thinking

This chapter adds a second way to read code. Earlier chapters ask what a component
means and which responsibility it owns. Here we ask how its computational cost
scales, where memory is retained, what actually becomes hot in Python, and how to
make performance decisions without damaging semantics or readability.

> **[KERNEL / GENERAL SOFTWARE]** Complexity analysis is a reasoning tool. The
> repository's actual performance decisions remain measurement-first; see
> [Performance Measurement](../../performance.md) and ADR
> [0004 — Prefer readability before micro-optimization](../../decisions/0004-readability-before-micro-optimization.md).

## Mental model: efficiency has several meanings

"Fast" is not one property.

```text
algorithmic complexity
    How does work grow as the problem grows?

constant-factor cost
    How expensive is each operation in this implementation?

frequency
    How many times does that operation execute?

allocation behavior
    What objects are created, copied, and retained?

measured performance
    What is actually expensive on a real workload?
```

A function can have excellent asymptotic complexity and still dominate a profile
because it executes millions of times. Another function can have worse Big-O and
be irrelevant because it runs once during startup.

## Start by defining the scaling variables

A statement like "this is O(n)" is incomplete until `n` has meaning.

Useful variables in this engine include:

| Symbol | Meaning |
| --- | --- |
| `T` | completed simulation steps |
| `S` | stages in one step |
| `P` | processes in one stage |
| `Q` | proposals produced in one stage |
| `R` | proposals accepted/resolved in one stage |
| `E` | events committed in one completed step |
| `N` | size of the modeled domain state |
| `K` | configured context services |
| `O` | observers/telemetry observers |

Domain algorithms need their own variables too: number of organisms, candidate
mates, spatial neighbors, loci, chromosome copies, resources, and so on.

### Why this matters

This line is one Python call:

```python
domain_state.copy()
```

But it might copy a world containing thousands of entities. One line of syntax is
not one unit of computational work.

## Big-O, Theta, and Omega

For this textbook, the most useful notation is:

- **O(f(n))** — an asymptotic upper bound;
- **Theta(f(n))** — the growth rate is bounded above and below by the same class;
- **Omega(f(n))** — an asymptotic lower bound.

You will most often see Big-O because it is a useful engineering shorthand. Use
Theta when the tighter statement is clear. Do not force precision that the
abstraction cannot justify.

### Common growth rates

```text
O(1)       constant
O(log n)   logarithmic
O(n)       linear
O(n log n) near-linear sorting-style growth
O(n^2)     pairwise/quadratic
O(2^n)     exponential
```

A tenfold increase gives rough intuition:

```text
O(1)        ~same amount of work
O(n)        ~10x
O(n log n)  somewhat more than 10x
O(n^2)      ~100x
```

Constants and real hardware still matter for practical runtimes.

## Big-O is not a stopwatch

Suppose:

```text
Algorithm A: 1000n
Algorithm B: n^2
```

`B` has worse asymptotic scaling, but for small enough `n` it can still be faster.
Big-O answers a scaling question, not "how many milliseconds will this take?"

That distinction is central to this repository. Profiling once showed that normal
`SimulationState` constructor validation contributed only a very small amount to a
fixed kernel workload. A second special trusted constructor could remove some work,
but the measured saving was too small to justify a second invariant path. The
algorithmic class was not the decision; measured value versus maintenance cost was.

## Best, average, and worst case

Complexity sometimes depends on the input.

For a hash-table lookup such as:

```python
dispatch = mapping[event_type]
```

the engineering model is **average O(1)** lookup. Pathological collision behavior
can be worse, but treating dictionary access as average constant time is the useful
model for ordinary engine analysis.

For a list membership test:

```python
candidate in values
```

the search may finish immediately in the best case but is O(n) in the worst case.

Always state which interpretation matters when ambiguity is important.

## Amortized analysis

Python list append is a classic example:

```python
items.append(value)
```

Most appends are cheap. Occasionally Python grows the underlying storage and moves
references. We therefore treat append as **amortized O(1)**, and appending `n`
items as O(n) total work.

Amortized analysis asks about the average cost across a sequence of operations,
not merely one unusually expensive operation.

## Useful Python container costs

These are conceptual engineering costs, not promises about every Python
implementation detail.

| Operation | Typical time | Extra memory |
| --- | ---: | ---: |
| `len(list)` | O(1) | O(1) |
| `items[i]` | O(1) | O(1) |
| `list.append(x)` | amortized O(1) | amortized growth |
| `x in list` | O(n) | O(1) |
| `mapping[key]` / `.get(key)` | average O(1) | O(1) per lookup |
| `list(sequence)` | O(n) | O(n) new reference storage |
| `tuple(sequence)` | O(n) | O(n) new reference storage |
| `sorted(sequence)` | O(n log n) | additional sorting storage |

A new list or tuple normally copies **references**, not the entire referenced
object graph.

## Time complexity versus space complexity

Consider:

```python
prepared = []
for event in events:
    prepared.append(materialize(event))
```

For `n` events, ignoring `materialize()` itself:

```text
time:        O(n)
extra space: O(n)
```

By contrast:

```python
for event in events:
    apply(event)
```

can use O(1) auxiliary container space while still taking O(n) time, again excluding
work performed by `apply()`.

### Auxiliary space

When discussing an algorithm, **auxiliary space** means additional memory needed
beyond the input/output structures themselves.

A simulation may already own a large world. Asking how much additional memory one
stage requires is often more useful than saying "the entire simulation uses O(N)
memory."

## References, shallow containers, and deep semantic copies

These operations are easy to confuse:

```text
reference assignment
    another name points at the same object

new shallow container
    new list/tuple, same referenced child objects

semantic/deep copy
    new independent modeled objects according to domain copy semantics
```

For example:

```python
events_tuple = tuple(applied_events)
```

creates O(E) new tuple reference storage for `E` events; it does not duplicate all
`AppliedEvent` objects.

`SimulationState.copy()` is different because it asks the domain payload to create
an independent transactional copy.

## Compositional complexity analysis

Abstractions often delegate work. Do not hide that work behind a misleading
single complexity label.

For `SimulationState.copy()`:

```text
time = C_domain_copy(N) + fixed-size RNG clone + envelope construction
space = M_domain_copy(N) + cloned RNG state + new envelope
```

The kernel cannot state whether `C_domain_copy(N)` is O(N), O(N log N), or something
else because `domain_state` is deliberately opaque.

Similarly, a stage's total cost is better expressed as:

```text
sum of proposal algorithm costs
+ kernel proposal aggregation
+ resolver cost
+ sum of accepted-event materialization costs
+ application costs
+ telemetry/effect overhead
```

Good complexity analysis exposes unknown delegated costs rather than pretending
they do not exist.

## Frequency layers

The same operation matters differently depending on how often it runs.

```text
once per configuration
once per simulation
once per step
once per stage
once per proposal
once per accepted event
once per entity
once per entity pair
once per locus
```

A moderately expensive preflight executed once may be irrelevant to runtime. A
small allocation executed once per accepted event can dominate a long simulation.

A useful first approximation is:

```text
total cost ~= cost per operation x frequency
```

## What is a hot path?

A **hot path** is code that contributes materially to runtime because it executes
frequently, is expensive per execution, or both.

Do not confuse:

```text
architecturally important
computationally expensive
frequently executed
measured hotspot
potential scaling hazard
```

They are different properties.

`SimulationSpec.compile()` is architecturally important but normally startup work.
`AppliedEvent` construction is conceptually simple but occurs once per committed
event and has appeared as a measurable generic per-event cost in kernel profiling.

## Three levels of performance reasoning

### 1. Algorithmic performance

Examples:

- scanning `N` entities: O(N);
- sorting `Q` proposals: O(Q log Q);
- considering every unordered entity pair: O(N^2).

### 2. Structural Python overhead

Examples:

- repeated runtime protocol inspection;
- repeated type-name construction;
- unnecessary conversions;
- temporary object allocation;
- repeated dictionary/list work.

These can improve real performance without changing Big-O.

### 3. Runtime/hardware effects

Examples include interpreter overhead, allocator behavior, and CPU/cache effects.
Know that they exist, but this textbook focuses primarily on algorithmic and
Python-structural reasoning.

## Profiling, benchmarking, and memory measurement

These answer different questions.

| Method | Question |
| --- | --- |
| complexity analysis | How does cost scale? |
| profiling (`cProfile`/`pstats`) | Where did this run spend time? |
| benchmarking (`pyperf`, repeated timing) | How fast is this controlled operation/workload? |
| allocation profiling (`tracemalloc`) | Where are Python allocations and what is peak traced memory? |

The repository deliberately uses domain-neutral synthetic kernel profiles for
kernel claims and reference-ecology profiles for end-to-end signals. Biological
work inside a reference simulation must not be mislabeled as kernel overhead.

## Memory lifetime matters

Space complexity alone does not tell the whole story.

Think in four categories:

```text
persistent domain state
    lives across the simulation

transactional duplication
    working state copy, typically one step

stage temporaries
    proposals/resolved/prepared structures, typically one stage

historical retention
    recorder snapshots, telemetry history, exports, pedigree data
```

Two O(N) structures can have very different practical consequences if one exists
for milliseconds and the other is retained for every step of a long experiment.

When analyzing memory, record both **size growth** and **lifetime**.

## Observability has a cost

Observation and telemetry improve scientific usefulness and debugging, but can
add:

```text
CPU work
allocations
memory retention
serialization
storage
```

An observer retaining an O(N) population snapshot for `T` steps can accumulate
O(TN) historical data even if the simulation's live state remains O(N).

This is not an argument against observability. It is a reminder to distinguish
scientific value from computational cost and measure the layer that is actually
expensive.

## Time-space tradeoffs

Caching often spends memory to save repeated work.

`StageCoordinator` caches process dispatch metadata. With `P` configured processes,
that uses O(P) stable metadata but supports average O(1) event-type-to-process
lookup per accepted event instead of repeatedly searching or performing runtime
inspection.

The right question is not "is caching faster?" but:

```text
Is the repeated work frequent enough?
Is the cached information genuinely stable?
How much memory/complexity does the cache add?
Does the cache preserve semantics?
```

## Semantics-sensitive optimization

Classify proposed optimizations by risk.

```text
STRUCTURALLY SAFE
remove repeated work whose value is stable

SEMANTICS-SENSITIVE
change ordering, RNG timing, state visibility, or dynamic capability checks

ARCHITECTURE-CHANGING
change representation or public contracts
```

The evidence bar should rise from the first category to the third.

For this engine, moving stable dispatch discovery out of a per-event loop can be a
safe structural optimization. Materializing events before resolution would be a
semantic change because rejected candidates would consume work/randomness and the
stage contract would change.

## Premature optimization: the useful version

Do not interpret "avoid premature optimization" as "never think about
performance."

A better rule is:

> **Reason about scaling early; optimize implementation details when evidence
> justifies them.**

If a proposed scientific algorithm contains an obvious O(N^2) all-pairs loop, notice
that immediately. Whether you should redesign it depends on expected scale,
scientific semantics, available data structures, and measurement.

## Optimization decision tree

```text
Is performance actually a problem?
        |
       no -> stop
        |
       yes
        v
Can the workload be reproduced?
        |
        v
Profile the correct layer
        |
        v
What dominates?
   /                 \
algorithm/data      repeated constant work
structure              / allocation
   |                       |
   v                       v
improve algorithm?     remove repetition?
better data structure? reduce allocation?
   \                       /
    +----------+----------+
               v
      measure before/after
               |
               v
Did semantics/readability/maintainability degrade?
        /                 \
      yes                  no
       |                    |
    reject          consider the change
```

## Performance budgets by frequency

You can tolerate more setup work in code that executes once than in code that
executes for every entity pair in every step.

When reviewing a function, write down both:

```text
cost per invocation
frequency per run
```

Then ask what happens when the important scientific scale variables grow 10x.

## Scientific-model complexity

Sometimes high complexity reflects the mathematical model, not poor software.

If every organism truly must compare with every other organism, a direct model can
be O(N^2). The engineering question becomes whether an equivalent scientific result
can be achieved with neighborhoods, indexing, caching, or another algorithm without
changing the model's meaning.

Never optimize by silently changing the science.

## Reproducibility and performance comparison

A benchmark is meaningful only when it compares like workloads.

For stochastic simulations, prefer:

```text
same seed
same configuration
same software/environment where practical
same outcome dimensions
same modeled workload semantics
```

If one run processes fewer events because the stochastic outcome changed, a lower
wall-clock time does not prove the implementation is faster.

## Misconception check

**"This operation is O(1), therefore it cannot be a hotspot."**

False. O(1) describes scaling per invocation. A constant-time operation can be
expensive or execute millions of times.

**"Two O(n) implementations have the same performance."**

False. They have the same asymptotic growth class. Constant cost, allocation,
Python dispatch, and memory behavior can differ substantially.

**"The longest function is probably the hottest."**

False. Hotness is empirical/frequency-based, not visual complexity.

**"A faster implementation is automatically better."**

False. Correctness, semantic stability, readability, maintainability, and measured
benefit all matter.

## You understand this chapter if you can...

- define the scaling variables before assigning a complexity class;
- distinguish Big-O from profiling and benchmarking;
- analyze delegated work compositionally instead of hiding it;
- distinguish auxiliary memory, retained memory, and memory lifetime;
- explain why an O(1) operation can be a measured hotspot;
- identify a time-space tradeoff in real engine code;
- explain when performance reasoning should happen before profiling and when
  optimization should wait for evidence; and
- reject an optimization that improves a microbenchmark while damaging simulation
  semantics or maintainability.

## Next

Continue to [Simulation Fundamentals](simulation_fundamentals.md), then revisit
these tools in [Engineering Anatomy of the Kernel](kernel_engineering_anatomy.md).
