# WB6 Handoff — Diagnostics and Support-Envelope Hardening

WB6 should harden the Evolution Experiment Workbench only where WB1–WB5 produced
real user-facing or architectural friction. It should not become a generic
Workbench-framework milestone.

Use current `main`, `AGENTS.md`, the Workbench architecture, the WB1–WB5 concrete
contracts, tests, Issues/PRs, and CI as authority before implementation.

## Goal

Improve diagnostics and support-envelope behavior so a user can understand:

```text
what is incomplete?
what is unsupported?
what evidence is missing?
what scientific identity was lost?
what exact-reproduction compatibility failed?
what can the user do next?
```

without moving lower-layer validation authority into Workbench and without parsing
arbitrary Python exception prose into invented scientific meaning.

## Real friction observed in WB1–WB5

### 1. Readiness and support diagnostics are concrete but repeated

WB1 introduced small structured `WorkbenchDiagnostic` readiness values for missing
and unsupported authoring choices. WB4 added richer recipe-local applicability,
support tiers, and stale inactive-state normalization. The repeated responsibility
is now real: users need stable Workbench-owned explanations for choices the
Workbench itself declares incomplete, irrelevant, or unsupported.

WB6 may consolidate only the repeated diagnostic semantics demonstrated by these
recipes. Do not create a universal validation framework.

### 2. Conditional authoring requires explicit irrelevant-state behavior

WB4 demonstrated real conditional controls:

- Gaussian spread is meaningful only for Gaussian movement;
- patch geometry is meaningful only for the two-patch geography;
- mutation parameters are meaningful only when mutation is enabled.

Inactive values must not silently survive into scientific meaning. WB4 normalizes
those stale values out. WB6 should make this behavior legible to users, for example
with a structured irrelevant-parameter diagnostic or explicit normalization notice
where that improves authoring UX.

### 3. Missing evidence needs scientific remediation, not inference

WB5 demonstrated a concrete post-run failure mode: a user may request an analysis
or presentation that requires evidence the run did not record. In particular,
reference-ecology world replay cannot be fabricated without spatial evidence.

The current downstream adapter can identify the missing evidence ID and explain
that the Study must be rerun with the appropriate EvidencePlan. WB6 should make
this a consistent structured remediation path for concrete existing consumers.

Do not introduce an evidence dependency solver. Concrete consumers should continue
to declare their bounded requirements.

### 4. Scenario origin and validated identity need consistent user-facing status

WB2 proved that a B3-derived radius-2 fork can retain B3 scientific origin while
losing canonical validated B3 identity. WB5 then demonstrated a downstream
consequence: that fork may be inspected descriptively but must not automatically
inherit the validated B3 representative story/headline-claim cinematic handoff.

This is a real candidate for a stable `SCENARIO_IDENTITY_LOST`-style Workbench
diagnostic with explicit explanation and remediation. It must not become a generic
claim-inference engine.

### 5. Exact reproduction failures need structured compatibility reporting

WB1/WB2/WB4 exact loading and compilation deliberately reject incompatible,
tampered, or stale manifests rather than silently re-resolving historical intent.
`IncompatibleManifestError` and recipe-specific checks preserve the science, but a
product user needs to know which compatibility boundary failed and whether the
available action is exact reproduction, fork/recompile as new science, or no
supported action.

WB6 should improve this only from the existing compatibility fields and errors. It
must not create an automatic migration system or pretend a modern recompile is an
exact historical reproduction.

### 6. Experiment integrity and counterbalance meaning must remain concrete

WB3 relies on existing E3/E4 treatment-integrity authority. E4 also keeps
founder-order counterbalancing separate from the primary environment factor. Any
Workbench diagnostic for factor or treatment-integrity failure must preserve that
concrete distinction and should not infer treatment meaning from arbitrary object
diffs.

A `TREATMENT_INTEGRITY_FAILURE`-style diagnostic is justified only as a thin wrapper
around existing experiment-specific integrity authority.

### 7. Presentation integration exposed dependency-guard wording friction

Before WB5, the architecture guard was phrased broadly as lower packages not
importing Workbench. WB5 established the full one-way architecture:

```text
model / evidence / experiments
        ↓
     Workbench
        ↓
   UI / cinematic
```

UI and cinematic are legitimate downstream Workbench consumers. The guard had to
be refined to allow that direction while separately preventing Workbench/model/
science from importing renderers.

This is settled architecture, not a reason to create a dependency framework.

### 8. Presentation-oriented bundles are not universal scientific results

WB5 found that the existing V2 `DashboardRun` shape is useful for its current UI but
is not the same responsibility as WB4 evidence or WB3/E3/E4 scientific results.
Forcing them into one result hierarchy would erase meaningful differences.

WB6 should resist diagnostics or support abstractions that assume every Study has
the same result/presentation shape.

### 9. High-volume evidence already has a real advisory case

WB4 spatial replay has storage/performance implications and already exposes a
non-blocking advisory. This is evidence that Workbench can distinguish blocking
readiness from advisory support information. WB6 may improve consistency of this
separation, but should not create a generalized cost-estimation engine.

## Candidate structured Workbench-owned diagnostics

The following names are useful starting points because they correspond to observed
responsibilities, not because WB6 must implement all of them as one enum:

```text
INCOMPLETE_CHOICE
UNSUPPORTED_CHOICE
IRRELEVANT_PARAMETER
MISSING_REQUIRED_EVIDENCE
SCENARIO_IDENTITY_LOST
INVALID_FACTOR_LEVEL
TREATMENT_INTEGRITY_FAILURE
EXACT_REPRODUCTION_UNAVAILABLE
```

Where a structured diagnostic is implemented, it should carry only fields needed by
real consumers, such as:

```text
stable code
severity / blocking status
semantic slot or concrete context
human explanation
supported remediation action(s)
```

Avoid putting lower-layer biology validity, generic dependency satisfaction, or
exception parsing into Workbench-owned semantics.

## Lower-layer boundary to investigate, not assume

Current lower preflight already has useful structured dependency information, but
some failure paths raise before a caller can inspect a complete structured report.
WB6 should first inventory actual WB1–WB5 cases where this prevents good user
remediation.

Only if repeated concrete cases require it should WB6 add the smallest non-raising
preflight/structured-failure seam. The Workbench must not duplicate genetic,
biological, generic dependency, or model-invariant validators.

## Support-envelope hardening

WB6 may promote an existing Advanced capability toward easier authoring only when
WB1–WB5 usage/tests show that its semantics, applicability, validation, and
persistence are already stable. Do not expose arbitrary Extension/Internal
capabilities merely to make the form look comprehensive.

In particular, WB6 is **not** authorization for:

- arbitrary genetics editing;
- arbitrary development/G×E editing;
- lifecycle/process graphs;
- reproduction-system composition;
- generic compatibility matrices;
- capability graphs;
- plugin systems;
- reflection-based form generation;
- universal experiment/result/presentation schemas.

## Suggested WB6 acceptance criteria

A strong WB6 should demonstrate the following against current concrete Workbench
verticals:

1. ordinary Workbench-owned incomplete/unsupported/irrelevant choices surface
   stable structured diagnostics with actionable remediation;
2. missing-evidence result/presentation requests identify the exact concrete
   evidence requirement and rerun action without fabricating science;
3. B3-derived loss of validated identity is explicit and remains distinct from
   scenario origin;
4. exact-reproduction incompatibility is distinguishable from ordinary authoring
   invalidity and from an intentional new fork/recompile;
5. experiment-specific treatment-integrity failures preserve concrete factor and
   counterbalance semantics;
6. advisory conditions remain distinct from blocking readiness;
7. lower biological/scientific validators remain authoritative and are not copied
   into Workbench;
8. no UI or renderer dependency leaks upward;
9. any promoted support capability is justified by demonstrated repeated use;
10. no diagnostic consumer parses free-form exception text to invent semantic
    remediation when a structured source is available.

## Workflow

Treat WB6 as a substantial repository milestone:

```text
Issue
  ↓
branch
  ↓
small diagnostics/support changes driven by evidence above
  ↓
early opened PR recovery checkpoint
  ↓
focused tests
  ↓
full CI
  ↓
exact-head review
  ↓
squash merge
  ↓
main verification
```

If current `main` has moved, repository truth overrides this handoff.
