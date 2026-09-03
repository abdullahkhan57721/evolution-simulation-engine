# Engineering Analysis Glossary Addendum

These terms supplement the main [Glossary](glossary.md).

**Algorithmic complexity** — A model of how computational cost grows as chosen
input/scale variables grow.

**Amortized complexity** — Average cost across a sequence of operations where
occasional expensive operations are spread over many cheap ones.

**Auxiliary space** — Additional memory an algorithm uses beyond the input/output
structures themselves.

**Benchmark** — Controlled measurement of how long or how much memory a chosen
operation/workload uses under specified conditions.

**Change radius** — The set of implementations, callers, tests, composition roots,
docs, and other surfaces likely affected by a change.

**Constant factor** — Per-operation cost hidden by asymptotic notation. Two O(n)
implementations can have very different constant factors.

**Cost model** — The assumptions used when treating operations as having certain
costs during complexity analysis.

**Hot path** — Code that contributes materially to measured runtime because of
execution frequency, cost per invocation, or both.

**Memory lifetime** — How long an allocation remains reachable/needed: expression,
stage, step, run, or retained experiment history.

**Peak memory** — Maximum memory in use at one point in a workload.

**Profiling** — Measuring where a particular execution spends time/calls rather
than predicting asymptotic growth.

**Retained memory** — Memory that remains reachable for later use rather than
being temporary allocation.

**Scaling variable** — A quantity such as entities, proposals, stages, steps, or
loci whose growth is relevant to complexity analysis.

**Structural overhead** — Work performed by orchestration/data-structure machinery
separate from delegated domain algorithms.

**Time-space tradeoff** — Spending additional memory to reduce repeated runtime
work, or accepting more work to reduce memory.

**Measured hotspot** — A runtime path supported by profiling evidence as materially
expensive for a specified workload.

**Potential scaling hazard** — Code whose asymptotic structure may become expensive
at larger scale even if current profiling does not yet show it as a hotspot.

**Control-flow locality** — How easily the important algorithm can be seen in one
coherent area of code.

**Fast-path explosion** — Multiple specialized implementations of the same
semantic algorithm created for small performance differences, increasing
maintenance risk.

**Semantic performance risk** — Risk that an optimization changes modeled meaning,
ordering, RNG timing, state visibility, or another correctness contract.
