# Performance Frequency Map

When scanning code for possible performance relevance, classify its execution
frequency before judging local complexity.

```text
CONFIGURATION TIME
SimulationSpec construction / dependency preflight
        |
        | once
        v
RUN TIME
SimulationEngine.run
        |
        | T steps
        v
STEP TIME
SimulationState.copy
SequentialStepCoordinator.coordinate
        |
        | S stages per step
        v
STAGE TIME
StageCoordinator.coordinate
        |
        | P processes / Q proposals / R accepted events
        v
EVENT TIME
materialize_event
apply_event
AppliedEvent creation
        |
        | domain-specific inner work
        v
ENTITY / PAIR / LOCUS TIME
biological/ecological algorithms
```

## Review habit

For every suspected optimization write:

```text
cost per invocation:
frequency:
scale variable:
measured share:
```

This prevents complex-looking startup code from distracting you from simple but
very frequent runtime work.
