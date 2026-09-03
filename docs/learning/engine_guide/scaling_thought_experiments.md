# Scaling Thought Experiments

Use these before profiling to build intuition about which dimensions can grow.
The answers are approximate because domain policies can change the exact costs.

## Ten times more simulation steps

If the per-step workload stays similar:

```text
T -> 10T
runtime -> roughly 10x
```

But if population or event counts grow with time, total work can grow faster than
linearly in `T`.

## Ten times more organisms in a linear scan

```text
O(N) scan
N -> 10N
work -> roughly 10x
```

Examples might include checking one simple condition for every organism.

## Ten times more organisms in all-pairs comparison

```text
O(N^2)
N -> 10N
pair work -> roughly 100x
```

This is why mate selection, competition, or interaction algorithms deserve early
scaling analysis even before they are measured hot.

## Ten times more proposals

For the kernel's linear proposal/preparation loops:

```text
Q -> 10Q
kernel list/iteration work -> roughly 10x
```

But resolver cost can grow differently. A sorting resolver can scale closer to
`Q log Q`; another conflict algorithm may have a different cost.

## Same proposals, lower acceptance rate

Suppose:

```text
Q = 100,000 proposals
R = 1,000 accepted
```

Accepted-only materialization means expensive deferred work scales with `R`, not
`Q`.

This demonstrates why phase semantics can matter computationally.

## Ten times more context services

An uncached tuple scan can require roughly ten times as many comparisons in the
worst case, but typed lookups already cached remain average O(1). Whether this is
important depends on `K`, lookup frequency, and measured runtime.

Do not redesign the configuration store from Big-O alone.

## Store every full population snapshot

If each snapshot is O(N) and you retain one for `T` steps:

```text
historical memory ~ O(TN)
```

If population size varies:

```text
memory ~ O(sum N_t)
```

This can dominate live simulation memory even though each snapshot individually is
only linear.

## Ten times more loci per organism

If a biological expression algorithm independently scans all loci, cost can grow
roughly linearly in locus count. If it considers interactions among all locus
pairs, the cost may grow quadratically.

The kernel does not change; the scaling belongs to the biological expression
algorithm.

## Ten times more chromosome copies

Ploidy-aware biological policies may have costs dependent on copy count, pairing,
and segregation algorithm. Again, define the biological variables rather than
calling the overall engine `O(N)`.

## Questions to ask for every 10x thought experiment

```text
Which variable changed?
Which loops/data structures depend on it?
Which lower-level costs remain unchanged?
Does memory persist or remain temporary?
Could a better algorithm/data structure preserve semantics?
At what expected scale does this become worth profiling?
```
