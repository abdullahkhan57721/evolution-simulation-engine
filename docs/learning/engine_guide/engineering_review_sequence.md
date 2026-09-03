# Engineering Review Sequence

When time is limited, review consequential code in this order:

```text
1. correctness / semantic invariant
2. ownership and layer boundary
3. tests
4. algorithm and scale variables
5. memory lifetime
6. execution frequency / profile evidence
7. readability
8. maintainability / change radius
9. extensibility / abstraction fit
10. optimization tradeoff
```

A fast implementation that fails steps 1–3 is not a candidate for approval.
