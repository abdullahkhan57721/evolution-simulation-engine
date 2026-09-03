# Observability Has a Cost

Observation and telemetry are part of scientific usefulness, not free side
features.

Potential costs include:

```text
per-step observer computation
per-event telemetry allocation
snapshot copying
serialization
file output
long-run retained histories
```

## Analyze the right question

Do not ask only:

> How much faster is the simulation without observers?

Also ask:

```text
Which observations are scientifically required?
Which data must be available after the run?
Can summaries replace raw snapshots?
Can raw data be streamed/exported instead of retained?
Which layer owns that retention choice?
```

## Memory example

If one full population snapshot is O(N) and an observer retains one for each of
`T` steps:

```text
approximately O(TN) history for stable N
```

or more generally:

```text
O(sum N_t)
```

The live simulation can remain O(N_t) while analysis history grows across the
whole experiment.

The repository's separate observed/unobserved reference performance scenarios make
this cost visible without blaming the kernel for observation work.
