# WB5 — Scientific Results and Presentation Integration

WB5 settles how a Workbench Study continues after execution without moving
scientific authority into the Workbench UI or renderer packages.

The durable direction is:

```text
semantic Study authoring
        ↓
exact saved revision / resolved manifest
        ↓
run action
        ↓
committed evidence
        ↓
existing scientific measurements and experiment results
        ↓
Study-facing result navigation
        ↓
existing renderer-neutral scientific meaning
        ↓
interactive or cinematic presentation
```

The Workbench does **not** become a second analysis system. `evo_engine.workbench`
associates existing scientific artifacts with exact Study, manifest, treatment,
replicate, and evidence identity. `evo_engine.ui` and `evo_engine.cinematic` are
explicit downstream consumers.

## Scientific authority boundary

Preserve:

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
scientific encoding
        ↓
presentation
```

WB5 does not allow a widget, chart implementation, renderer, or presentation
preference to define an authoritative metric, treatment, replicate, or scientific
reproduction identity.

`workbench.results` therefore contains navigation/association values rather than a
universal scientific result hierarchy. Existing E1, E3, E4, B3, observation, and
telemetry values remain authoritative.

## Result navigation

`AnalysisAvailability` is deliberately small. It records one concrete consumer's
existing evidence requirements, any missing evidence IDs, and an optional bounded
reason the view is unavailable. It is not an evidence registry or dependency
solver.

The current Study-facing result views cover four concrete cases:

1. **WB1 controlled locomotion** — keeps the run attached to the exact
   `StudyRevision`, resolved manifest, EvidencePlan, `ScientificRunProvenance`,
   population observations, and existing E1 locomotion measurements. If committed
   movement events were not recorded, locomotion analysis remains unavailable.
2. **WB3 E3-style max-speed sweeps** — keeps each existing `E3ReplicateOutcome`
   attached to the authored semantic max-speed factor level, seed, treatment ID,
   and exact expanded manifest. Existing `E3TreatmentSummary` values pass through
   unchanged.
3. **WB3 E4-style environment comparisons** — keeps the environment factor,
   control/treatment role, seed, standing focal composition, founder-order
   counterbalance, full existing `E4ReplicateOutcome`, and existing environment
   summaries distinct. Counterbalancing never becomes a factor and full
   composition is not collapsed into mean `max_speed`.
4. **WB2 curated B3** — keeps confirmation, radius sensitivity, and founder-label
   counterbalance artifacts in separate roles. Scenario origin remains distinct
   from validated scenario identity.

These views make results navigable without recoding E1/E3/E4/B3 science in the
Workbench.

## Evidence insufficiency is explicit

A presentation or analysis can use only evidence that the producing run actually
recorded. WB5 does not reconstruct missing events from snapshots, infer individual
genetics from population summaries, reconstruct pedigree from current state, or
pretend an unrecorded spatial history can be regenerated from a finished run.

For the bounded reference ecology, interactive world replay therefore requires the
existing spatial evidence selection. If it was not recorded, the downstream V2
adapter reports the missing evidence and tells the caller that the Study must be
rerun with the appropriate EvidencePlan.

This is a scientific boundary, not merely a UI limitation.

## Interactive presentation

`evo_engine.ui.workbench` is downstream of Workbench science. It builds the existing
V2 `WorldPresentationFrame` from committed evidence and keeps the exact
`WorkbenchRunProvenance`, seed, and, for B3, matched arm/environment identity beside
the frame.

For B3, matched control/treatment world views share the existing renderer-neutral
`ContinuousTraitEncoding` for `max_speed`. Presentation toggles such as resource or
trail visibility affect only the produced view. They do not mutate or contribute to
the saved scientific manifest.

WB5 intentionally does not turn the older `DashboardRun` type into a universal
Workbench result. It is a presentation-oriented bundle for an existing UI path,
not the scientific persistence model for every Study.

## Cinematic presentation

`evo_engine.cinematic.workbench` is also downstream. It does not add a generic
cinematic director. A validated canonical B3 Workbench result can be handed to the
existing B3-specific cinematic director, which remains authoritative for the
representative seed, representative mechanism episodes, fixed scientific encoding,
confirmation structure, radius sensitivity, bounded conclusion, and scope
qualifier.

The path is:

```text
exact B3 Workbench run artifacts
        ↓
existing B3 scientific handoff
        ↓
existing B3-specific director
        ↓
renderer-specific cinematic choreography
```

A radius-2 B3-derived fork retains B3 scientific origin but has no validated B3
scenario identity. WB5 therefore prevents that fork from automatically inheriting
the canonical radius-1 B3 representative story or headline-claim cinematic
handoff.

## Dependency direction

WB5 exposes the intended full direction mechanically:

```text
model / kernel / evidence / experiments
                ↓
             Workbench
                ↓
        +-------+-------+
        |               |
        v               v
       UI            cinematic
```

Lower model/science packages do not import Workbench. Workbench does not import UI
or cinematic packages. UI and cinematic packages may import Workbench because they
are downstream consumers.

This required refining the earlier architecture test: "lower packages do not
import Workbench" cannot be interpreted as "presentation consumers may not import
Workbench." The inverse boundary remains closed.

## Study product model audit

The WD2 product model works as a navigation model without requiring one Python
class per section.

| Product concept | Durable/persisted responsibility | Existing scientific contract or view | Action / downstream responsibility |
| --- | --- | --- | --- |
| **Study** | Recipe-specific immutable revision, lineage, exact manifest, EvidencePlan, completed-run provenance | Product container/navigation concept; no universal Study root is earned | Fork, diff, run, navigate |
| **Simulation** | Semantic authoring intent plus exact resolved scientific manifest | Existing typed/scenario composition reconstructed at compile time | Compile and execute are actions; mutable spec/engine/runtime graphs are not persisted |
| **Evidence** | Evidence intent is persisted in the concrete Study revision | Existing recorder outputs, telemetry, and observation contracts | Recording occurs during execution; availability afterward is a view |
| **Experiment** | Concrete WB3 experiment definitions persist their factor levels, seeds, roles, and pattern meaning | Existing E3/E4 treatment/outcome/summary contracts remain authoritative | Deterministic expansion and execution are actions |
| **Results** | Run provenance/references persist where existing Study contracts already do so; WB5 adds no universal persisted Results root | Primarily Study-facing views over existing evidence, measurements, replicate outcomes, and summaries | Inspect, compare, select replicate/treatment |
| **Presentation** | No new WB5 presentation preference persistence is required by the current product workflow | Existing renderer-neutral scientific encodings and scenario-specific handoffs | UI view state, overlays, selection, camera, timing, rendering, export quality, colors, frame rate |
| **Run** | Completed run provenance and scientific artifacts persist/reference exact producing science | Existing run/scientific provenance | **Run is an action**, not a top-level configuration section |

No presentation settings are intentionally persisted by WB5. Consequently there is
no presentation-preference save/load schema to test. The relevant invariant is
stronger and simpler for the current product: changing view options leaves the
scientific manifest unchanged.

## Answers to the WB5 architecture questions

### 1. Which Study sections need durable persisted values?

Simulation authoring intent, the immutable resolved manifest, EvidencePlan,
recipe/scenario lineage and identity, concrete WB3 experiment definitions, and
completed-run provenance need durable values. They are already persisted in the
appropriate recipe/pattern-specific contracts. WB5 did not discover a need for a
new universal Study or Results persistence root.

### 2. Which sections are views over existing contracts?

Results is primarily a view/navigation concept. Evidence availability after a run
is also a view over the recorded EvidencePlan and produced artifacts. Scientific
interpretation is reused only where an existing concrete experiment/scenario has
already earned it.

### 3. Which sections are downstream artifacts?

Interactive `WorkbenchWorldPresentation` values and B3 cinematic director plans are
downstream artifacts. Rendered frames, video, charts, UI panels, selections, and
exports remain farther downstream.

### 4. Which responsibilities remain renderer-specific?

Camera behavior, timing, interpolation, animation quality, frame rate, visible
panels/overlays, resource/trail visibility, selected-organism focus, colors,
materials, layout, chart styling, and export/render quality remain UI/cinematic or
renderer responsibilities. None belongs in a scientific manifest.

### 5. Is a new renderer-neutral presentation abstraction earned?

No. The existing `ContinuousTraitEncoding` and scenario-specific scientific
handoffs cover the shared renderer-neutral responsibilities exercised by WB5. A
universal `ScenarioPresentationSpec`, scene graph, or presentation schema would
have no demonstrated second responsibility to own.

### 6. Can one Study span authoring → experiment → results → presentation cleanly?

Yes. It does so by composition rather than a one-class-per-section hierarchy:
recipe-specific persistence owns scientific identity, existing experiments own
scientific outcomes, thin result views organize those outcomes, and UI/cinematic
adapters consume them downstream. Dependency tests enforce the direction.

## What WB5 did not generalize

WB5 does not introduce a metric registry, chart registry, generic evidence solver,
statistics framework, automatic claim generator, universal result type, universal
scene graph, universal presentation specification, generic cinematic director, or
new modeled biology.

The next Workbench milestone should harden diagnostics and support boundaries only
from concrete WB1–WB5 friction. See
`docs/development/wb6_workbench_handoff.md`.
