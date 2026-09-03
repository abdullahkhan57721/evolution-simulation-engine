# Source Analysis Method

Use this method when the goal is not merely to understand what a function does,
but to evaluate it as production software.

## Pass 1 — Semantic skeleton

Ignore most private helpers. Find:

```text
public entry point
inputs
outputs
mutation
control-flow phases
commit/observation boundaries
```

Write the algorithm in five lines of pseudocode.

## Pass 2 — Contracts and invariants

Read:

```text
Protocol/docstring
focused tests
ADR/authoritative subsystem doc when relevant
```

State the promises in your own words.

## Pass 3 — Ownership and authority

Mark:

```text
what object owns state
what component chooses
what component mutates
what component configures
what component merely observes
```

Many architecture mistakes become obvious here.

## Pass 4 — Complexity

Define variables before notation.

```text
P processes
Q proposals
R accepted events
N domain size
...
```

Then separate:

```text
local structural work
+
delegated/pluggable work
```

Never hide an arbitrary callback behind O(1) merely because it is one line.

## Pass 5 — Memory behavior

List:

```text
persistent state
temporary containers
copies
caches
telemetry/history
```

For each, write:

```text
size growth
lifetime
```

## Pass 6 — Frequency/hotness

Ask how often each operation occurs:

```text
startup
run
step
stage
proposal
accepted event
entity
pair
locus
```

Then consult profiling evidence before calling something a real hotspot.

## Pass 7 — Readability

Check:

```text
control-flow locality
naming
branch count
hidden dependencies
abstraction fit
cognitive load
```

## Pass 8 — Maintainability/change radius

Ask:

```text
How many semantic paths exist?
How public is this contract?
What depends on it?
What tests localize changes?
What rules are duplicated?
```

## Pass 9 — Extensibility

Ask what can vary behind current contracts and whether a proposed abstraction
corresponds to a real axis of change.

## Pass 10 — Optimization boundary

Identify tempting shortcuts and classify them:

```text
structurally safe
semantics-sensitive
architecture-changing
```

## Final one-paragraph explanation

After all ten passes, summarize the component as:

> **Purpose → core invariant → algorithm → scaling → memory → main tradeoff.**

For example:

> The step coordinator creates a transactional copy, runs ordered stages against
> it, gathers committed-event telemetry, advances the step index, and returns the
> completed candidate state. Its cost is dominated by domain copying and delegated
> stage work rather than the stage loop itself. The design pays copy time/memory to
> obtain simple rollback and RNG isolation, while keeping the control flow highly
> readable and extensible through stage composition.

If you can produce that paragraph without the guide, you understand the component
at a professional review level.
