# Complexity Quick Reference

Keep this page beside the source only after you understand the deeper complexity
chapter.

## Common symbols

```text
T = completed steps
S = stages per step
P = processes per stage
Q = proposals per stage
R = accepted events per stage
E = committed events per step
N = domain-state scale
K = context services
```

## Common Python costs

```text
len(list)              O(1)
list[i]                O(1)
list.append(x)         amortized O(1)
x in list             O(n)
dict[key] / get       average O(1)
list(sequence)         O(n) time + O(n) refs
tuple(sequence)        O(n) time + O(n) refs
sorted(sequence)       O(n log n)
```

## Kernel structural costs

```text
SimulationState.copy()
    time:   C_domain_copy(N) + fixed kernel overhead
    memory: M_domain_copy(N) + fixed envelope/RNG state

SequentialStepCoordinator
    time:   C_domain_copy(N) + sum(stage costs) + O(E)
    memory: M_domain_copy(N) + O(E) + stage temporaries

StageCoordinator
    time:   O(P + Q + R) + resolver cost
            + delegated process/materialization/application costs
    memory: O(Q + R) + telemetry/effects

SimulationEngine.run()
    time: sum across T steps of stopping + step + observation costs
```

## Do not forget frequency

```text
once per configuration
once per run
once per step
once per stage
once per proposal
once per accepted event
once per entity
once per entity pair
once per locus
```

## Do not confuse

```text
Big-O      -> scaling model
profiling  -> where one run spends time
benchmark  -> controlled before/after speed
tracemalloc -> Python allocation/peak-memory evidence
```

## Memory lifetime

```text
persistent domain state     run-long
transactional copy          step-local
proposals/prepared events   stage-local
observer history            potentially run-long and cumulative
```

## Review rule

Never write `O(n)` until you can answer:

> What is `n`, what delegated work is excluded, what memory is retained, and how
> often does this path run?
