# Complexity Walkthrough: One Stage

This worked derivation demonstrates how to build a complexity expression instead
of guessing a single Big-O.

Let:

```text
P = configured processes
Q_i = proposals emitted by process i
Q = sum(Q_i)
R = accepted events
```

## Propose

Kernel loop visits `P` processes and extends one proposal list with `Q` total
references:

```text
kernel structural time: O(P + Q)
proposal storage: O(Q), stage-local
```

Keep domain proposal algorithms explicit:

```text
+ sum(C_propose_i)
```

## Resolve

Generic stage cannot know the resolver algorithm:

```text
+ C_resolver(Q)
+ M_resolver(Q)
```

## Prepare / materialize

For `R` accepted events:

```text
average O(1) dispatch each -> O(R)
prepared storage -> O(R), stage-local
+ sum(C_materialize_j)
```

## Apply / telemetry

```text
O(R) kernel iteration
+ sum(C_apply_j)
+ effect journal costs
+ O(R) committed telemetry records/references
```

## Combined expression

```text
Time ~=
    O(P + Q + R)
    + sum(C_propose_i)
    + C_resolver(Q)
    + sum(C_materialize_j)
    + sum(C_apply_j)
    + effect/telemetry constant work

Stage-local structural memory ~=
    O(Q + R)
    + resolver/domain temporaries
```

This is more honest and useful than saying "StageCoordinator is O(n)."
