# Complexity Notation Used in This Guide

The guide uses asymptotic notation as a model, not as a substitute for profiling.

```text
O(f(n))     asymptotic upper bound
Theta(f(n)) tight growth class when justified
Omega(f(n)) asymptotic lower bound
```

Common local variables:

```text
T steps
S stages
P processes
Q proposals
R accepted events
E committed events
N domain-state scale
K context values
```

A function that delegates arbitrary work is written compositionally, for example:

```text
O(P + Q + R)
+ resolver_cost(Q)
+ sum(process costs)
```

rather than assigned a misleading universal class.
