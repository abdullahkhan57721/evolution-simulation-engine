# Memory Analysis for Simulations

Simulation programs deserve more nuanced memory analysis than a single Big-O label.
This page gives a vocabulary for reading the engine's memory behavior.

## Four memory categories

```text
1. Persistent modeled state
   entities, genomes, world structures, resources, etc.

2. Transactional duplication
   working state created for a step

3. Per-stage temporaries
   proposals, accepted-event/preparation structures

4. Historical retention
   telemetry histories, population snapshots, pedigree/observation records, exports
```

The same asymptotic size can have very different practical effects depending on
lifetime.

## Size plus lifetime

Record memory as two questions:

```text
How does the amount grow?
How long is it retained?
```

Example:

```text
proposal list
    size: O(Q)
    lifetime: stage

working domain copy
    size: M_domain_copy(N)
    lifetime: step candidate / committed state if returned

observer storing full population each step
    size per snapshot: O(N_t)
    cumulative lifetime: experiment
```

## Peak memory versus retained memory

**Peak memory** is the maximum memory occupied at one point in time.

**Retained memory** is memory that remains reachable for later use.

A stage may allocate many temporary objects and release them quickly, raising peak
memory without creating long-run growth. A recorder may allocate less per step but
retain everything, creating steady cumulative growth.

## Container copies versus object copies

```python
new_tuple = tuple(events)
```

creates a new container containing references to existing events.

Conceptually:

```text
new reference storage: O(E)
deep event duplication: none
```

By contrast, a domain's `copy()` may construct an independent graph of modeled
objects. Its cost must be analyzed according to the domain's copy semantics.

## Caches

A cache adds retained memory to reduce repeated work.

Evaluate:

```text
maximum cache size
cache lifetime
whether keys/values keep large object graphs alive
whether cached information is semantically stable
hit frequency
```

The kernel's small stable dispatch/context caches are different from an unbounded
memoization table keyed by evolving entities.

## Telemetry and observation

One `AppliedEvent` record is small relative to a large world, but millions of
retained events can become significant.

Likewise:

```text
store aggregate allele counts
```

can be far cheaper than:

```text
store every full genome snapshot for every organism at every step
```

Choose observation granularity according to scientific need, not only convenience.

## Streaming versus retaining

For long experiments ask whether results must all remain in memory.

Options can include:

```text
retain all data in memory
retain summaries only
stream/export records incrementally
periodically aggregate and discard raw detail
```

The correct choice belongs to experiment/observation design rather than changing
the kernel's state semantics.

## `tracemalloc`

When Python allocation is a suspected bottleneck, `tracemalloc` can attribute
Python-managed allocations and report peak traced memory for controlled workloads.

It answers a different question from asymptotic analysis:

```text
space complexity:
    how memory grows with scale

tracemalloc:
    which Python allocation sites contributed in this measured workload
```

## Memory-review checklist

```text
What is the dominant persistent state?
What gets copied transactionally?
What temporary containers exist per stage?
What objects are retained after commit?
What histories grow with T?
Are containers copying references or full objects?
Are caches bounded and semantically valid?
Could observation data be aggregated/streamed?
What scale variable drives peak memory?
Would tracemalloc answer a real unresolved question?
```
