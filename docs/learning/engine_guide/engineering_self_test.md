# Engineering Self-Test

Without opening the guide, answer:

1. Why is `SimulationState.copy()` not universally O(1)?
2. Why can an O(1) per-event operation be a hotspot?
3. Give a structural complexity expression for one stage using `P`, `Q`, `R`.
4. What is the difference between stage-local O(Q) memory and run-retained O(TN)
   observation history?
5. Why is materialize-after-resolution a semantic rule with possible performance
   benefits?
6. Name a structurally safer optimization and a semantics-sensitive one.
7. How do profiling and Big-O answer different questions?
8. What makes code readable beyond being short?
9. What makes a public-contract change expensive to maintain?
10. How do you decide whether new biology belongs in the kernel?
11. Why can a tiny startup graph traversal be irrelevant next to constant-time
    per-event work?
12. When should performance optimization stop?

If you cannot generate the reasoning yourself, use the relevant focused chapter
rather than rereading everything.
