# Source Complexity Notes

These short notes are intended to sit beside the detailed source walkthrough.

```text
protocols.py
    contracts only; complexity belongs to implementations

simulation_state.py
    copy cost dominated by opaque domain-state copy; once per step

simulation.py
    initial setup/copy; not event-hot

step_coordinator.py
    transaction + sum(stage costs); do not call it merely O(S)

stage_coordinator.py
    linear structural event flow plus pluggable resolver/process costs; per-event hot path

simulation_engine.py
    sum of step + observation costs across run

context.py
    uncached linear service scan, typed successful lookup cache; usually small immutable configuration

configuration/spec.py
    preflight/startup; frequency matters more than visual complexity

telemetry/records.py
    constant structural work per record but high event frequency can make allocation measurable
```
