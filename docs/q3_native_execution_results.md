# Q3 Native Execution and Results

Q3 completes the first native `Run → Results` path across all five concrete
Evolution Experiment Workbench Study families while preserving existing scientific
ownership.

## Architectural result

The native execution dependency remains:

```text
Qt Quick / QML
        ↓
RunController / ResultsController
        ↓
frontend-neutral Workbench execution + WB5 inspection
        ↓
existing concrete scientific runners and result types
        ↓
biology
        ↓
frozen kernel
```

Neither Qt nor the desktop package owns a new scientific Study, experiment, result,
or statistics schema.

## Exact pre-run ownership

Run never executes mutable frontend draft state as if it were persisted science.
Before the Run Plan opens, `ApplicationController` resolves the active concrete
family explicitly:

- controlled Simulation and Evidence drafts are combined into one immutable
  `StudyRevision` child;
- Reference Simulation and Evidence drafts are normalized and combined into one
  immutable `ReferenceStudyRevision` child;
- pending E3/E4 experiment edits become the exact immutable concrete experiment
  definition;
- B3 remains its exact curated `B3StudyRevision`.

This is deliberately atomic for revision-backed Studies. A user changing Simulation
and Evidence before Run gets one child scientific owner containing the complete
pending state rather than an incidental chain of intermediate revisions.

## Reviewable Run Plan

`RunController` exposes only transient application values needed to review execution:
scientific owner identity, manifest or experiment meaning, requested evidence,
treatment/replicate expansion where applicable, and concrete advisories. E3 and E4
rows come from the existing Workbench expansion contracts. B3 case counts come from
the existing curated compilation contract.

The Run Plan does not resolve a second simulation configuration and does not infer a
generic experiment representation.

## Off-GUI-thread execution

The five existing synchronous Workbench runners are reached through
`evo_engine.workbench.execution`. That dispatcher became frontend-neutral only after
Streamlit and Qt both needed the same concrete routing responsibility.

A narrow Qt worker runs the dispatcher on a `QThread`. Q3 does **not** introduce a
generic background-job system, cancellation protocol, queue, progress model,
multiprocessing layer, or distributed execution API.

A completed result is accepted only while the exact source scientific owner is still
active and the existing Workbench/WB5 association rules accept the returned result.
Revision-backed run provenance is then attached through the existing immutable
`with_run(...)` contracts.

## Family-specific Results

`ResultsController` uses the common product rhythm `Overview / Explore / Analysis /
Provenance`, but the underlying scientific meaning remains concrete by family.

### Controlled locomotion

Results expose recorded population observations and the existing E1 locomotion
measurement only when the corresponding EvidencePlan permits them.

### Reference Ecology

Population, committed events, pedigree/life history, genetic composition, and
spatial replay retain independent availability. Missing evidence remains explicitly
unavailable. Native world rendering still requires actual recorded spatial evidence;
it never reconstructs an unrecorded world.

### E3 max-speed sweep

Results preserve maximum speed as the factor and retain factor level, replicate seed,
treatment identity, manifest identity, and the existing `E3TreatmentSummary` values.

### E4 environment-selection comparison

Results preserve resource geography as the factor while keeping control/treatment
role, replicate seed, standing focal composition, and founder-order counterbalance
separate. Existing `E4EnvironmentSummary` values remain authoritative.

### B3 flagship

Results preserve scenario origin separately from validated canonical scenario
identity. Primary confirmation, radius sensitivity, and founder-label
counterbalance remain separate scientific result families. The existing cinematic
handoff availability is passed through rather than recalculated.

Matched B3 arms must never be presented as if their stochastic trajectories remain
lockstep after treatment-driven divergence; the shared seed is an experimental
blocking relationship, not a claim of identical RNG consumption.

## Historical run references

Persisted revision run provenance is not a persisted observations/result archive.
Reopening a Study may show that historical runs occurred, but Q3 does not regenerate,
reconstruct, or implicitly rerun their result payloads. Obtaining unavailable
analysis or replay requires a new explicit run with the required evidence.

## Native presentation handoff

Q3 settles the exact owner and result boundary that Q4 can consume. Q4 should broaden
Presentation from recorded evidence, beginning with richer Reference world
exploration and canonical B3 matched presentation/cinematic handoff. Renderer state
must remain downstream of committed evidence and scientific meaning; Q3 does not earn
a universal scene, camera, replay, or chart framework.
