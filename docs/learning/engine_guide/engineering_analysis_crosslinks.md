# Engineering Analysis Cross-Links

Core chapters should point into engineering analysis where it adds a new lens:

```text
SimulationState transaction explanation
    -> memory/copy tradeoff

StageCoordinator runtime explanation
    -> P/Q/R complexity + dispatch cache

Telemetry explanation
    -> per-event allocation + observer retention

SimulationContext explanation
    -> cache time-space tradeoff

SimulationSpec explanation
    -> startup frequency / graph-traversal reasoning

Worked examples
    -> distinguish kernel overhead from domain algorithm complexity
```

These are links to deeper analysis, not reasons to duplicate the same performance
paragraph in every chapter.
