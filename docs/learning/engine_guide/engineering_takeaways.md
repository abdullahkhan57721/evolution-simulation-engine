# Engineering Takeaways

If you remember only a few things from the engineering-analysis additions, remember
these:

```text
1. Define the scale variable before writing Big-O.
2. One line of Python can hide arbitrarily expensive delegated work.
3. Big-O describes scaling; profiling measures where a workload spent time.
4. Cost per operation × frequency often explains hot paths better than code size.
5. Analyze memory by both amount and lifetime.
6. The domain-state copy cost is deliberately domain-dependent.
7. Kernel orchestration cost must be separated from domain algorithm cost.
8. Accepted-only materialization protects semantics and can avoid rejected work.
9. Readability and maintainability are engineering constraints, not aesthetics.
10. More abstraction is not automatically more extensible or maintainable.
11. Optimize the measured structural problem in the correct layer.
12. Reject performance changes that silently alter RNG, ordering, or state visibility.
13. Tests tell you what must remain true; profiles tell you what is expensive.
14. A public-contract change can have a huge change radius despite few lines.
15. Stop optimizing when remaining gains are not worth the conceptual cost.
```

The transferable skill is to read code simultaneously as **behavior, architecture,
computation, and future maintenance burden**.
