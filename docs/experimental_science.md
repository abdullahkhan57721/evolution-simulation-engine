# Experimental Science Standard

This project separates modeled dynamics from scientific interpretation:

```text
modeled system
        ↓
committed state / committed events
        ↓
pure scientific measurement
        ↓
replicate outcome
        ↓
treatment comparison
        ↓
experiment-level reporting/export
        ↓
presentation
```

The purpose of this standard is to keep controlled experiments reproducible and
scientifically legible without turning the engine into a general statistics
framework.

## Experimental unit and inference

One complete simulation run under one seed is one experimental replicate.
Organisms within a run interact, share the same simulated environment, and descend
from common history. They are therefore dependent observations, not independent
replicates. Organism-level evidence can explain a replicate outcome, but
uncertainty or treatment comparisons across stochastic runs must preserve the run
as the replicate.

A simulation timestep is an update index, not automatically a biological
generation. Generation language is used only when the modeled reproductive
semantics justify it.

## Time and commit alignment

Events are stamped with the pre-step state index. After every stage succeeds, the
transaction increments the step once, commits the new authoritative state, and
emits telemetry. Therefore an applied event with `event_step_index = t` caused the
committed state at `t + 1`.

Failed transactions contribute neither state nor event evidence. Scientific
analysis must use committed telemetry rather than proposed or merely resolved
events.

When event evidence is compared with state observations, use this exact alignment:

```text
event step t  ──causes──>  committed state t + 1
```

## Evidence before measurement

Use this rule:

> Record evidence when it cannot reliably be reconstructed later; derive
> measurements from evidence whenever possible.

Domain processes calculate modeled consequences, not experiment statistics.
Observers and telemetry preserve authoritative evidence. Pure experiment-analysis
code derives scientific measurements from that evidence. UI and cinematic code
may present those measurements but never become their authoritative calculator.

For locomotion, for example:

- inherited `max_speed` is genetic capacity;
- the operative characteristic is realized/current capability;
- a movement event records the behavioral attempt and locomotion cost;
- `OrganismMoved` records the actual committed coordinate change;
- a scientific measurement derives realized displacement from the committed
  coordinate change.

These layers must not be collapsed into an ambiguous quantity such as "average
speed."

## Denominators and undefined quantities

Every average, rate, or proportion must name or document its denominator. Prefer
names such as `mean_realized_distance_per_applied_movement` or
`mean_locomotion_energy_expenditure_per_applied_movement` over ambiguous labels.

An empty denominator produces an undefined quantity, represented as `None` where
the typed result allows it. Do not silently replace undefined values with zero.
This matters especially after extinction: extinction is a substantive run outcome,
while post-extinction population trait means are undefined rather than zero.

## Exposure time and censoring

Lifetime, reproductive, and time-to-event measurements must preserve exposure.
An organism entering late or dying early does not automatically have the same
exposure time as a founder surviving the full assay.

Time-to-event comparisons use a fixed predeclared committed-state horizon. If
fixation, extinction, or another outcome is not observed by that horizon, record
the result as explicitly right-censored. Do not assign the horizon as though the
outcome happened there. `FixedHorizonTimeToEvent.observed_step_index` is the
committed-state index where the outcome was first observed; `None` means it was
unobserved and right-censored at `horizon_step_index`.

## Discovery, confirmation, and representative runs

Parameter or scenario discovery and independent confirmation are different
scientific roles. If discovery examines seeds or settings while selecting a
scenario, confirmation uses a frozen scenario and previously unexposed confirmation
seeds. A representative storytelling seed may be chosen for explanation after the
robustness result is known, but it is presentation evidence only and must not be
substituted for replicate-level robustness.

Same-seed treatment/control runs are a useful blocking design. They are described
as matched or blocked by seed. They are **not** claimed to be perfectly coupled
common-random-number replicates unless the stochastic architecture independently
establishes that stronger property.

## Evidence roles

Keep three evidence roles separate:

1. **Primary outcome** — the predeclared quantity that answers the experiment's
   central comparison.
2. **Mechanism evidence** — causal-chain measurements that explain how the primary
   outcome arose.
3. **Diagnostic evidence** — checks for integrity, implementation artifacts,
   boundary effects, anisotropy, extinction, or other threats to interpretation.

Likewise distinguish:

- stochastic robustness: repeated seeds under a fixed scenario;
- parameter sensitivity: changing numerical parameter choices;
- structural/mechanism sensitivity: changing modeled mechanisms or assumptions.

Success in one category does not imply success in the others.

## Treatment integrity

A concrete controlled experiment declares the one intended treatment difference.
Its treatment-integrity audit then replaces that declared difference with the
control value and requires the entire scientifically relevant frozen specification
to equal the control.

This project intentionally does not provide a generic configuration-diff DSL. The
experiment itself owns the scientific declaration of what is allowed to differ;
`validate_declared_treatment_difference` only performs the final equality check
after experiment-specific normalization.

## Provenance

Durable controlled-experiment results should carry `ScientificRunProvenance` or an
equivalent concrete value that identifies:

- experiment identity;
- scenario identity;
- treatment identity;
- canonical serialized scientifically relevant treatment specification;
- seed;
- fixed horizon;
- observation cadence, including whether committed step zero is recorded;
- selected focal variables;
- discovery, confirmation, or representative role when applicable.

Renderer metadata does not belong in scientific provenance.

## Measurement restraint

Add a measurement only when an experiment consumes it and authoritative evidence
supports it. Prefer immutable typed values and pure functions. Do not add metric
registries, metric-expression languages, universal analysis plans, dependency
solvers, or statistics-library dependencies merely to summarize simple evidence.

E1 proves this boundary with locomotion. E2 and E3 may add resource acquisition,
energy-balance, reproductive, or other measurements only when their concrete
experimental designs establish the required evidence and denominator semantics.
