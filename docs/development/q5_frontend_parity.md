# Q5 Frontend Parity and Streamlit Retirement Decision

Q5 closes the migration decision that began with WU1–WU5 and ADR 0010. The
PySide6 + Qt Quick application is the product frontend. The Streamlit implementation
is no longer a second product surface that must receive feature parity.

This decision is downstream of the existing Workbench and scientific contracts. It
does not change simulation, evidence, experiment, result, persistence, or
presentation semantics.

## Decision

**Option B: Qt is the primary product frontend; the sophisticated Streamlit
Workbench is deprecated.**

The existing `evo_engine.ui` implementation is retained temporarily as frozen
regression/reference material rather than deleted in Q5. No new product capability
should be implemented there, and future milestones do not owe it parity. Physical
removal can occur after the native human release audit has been completed and any
remaining compatibility value has been deliberately migrated or discarded.

This is intentionally different from maintaining two full frontends. There is one
product frontend and one deprecated reference implementation.

## WU1–WU5 parity audit

| Workflow / contract | Native Q5 status | Classification | Notes |
| --- | --- | --- | --- |
| Home, New Study, Open Study | Native Home/New/Open routes and file dialog | Improvement | No browser/session prerequisite. |
| Five concrete Study families | Same controlled, E3, E4, B3, and Reference routing | Parity | No generic Study persistence wrapper added. |
| Exact concrete persistence | Native Open, Save, Save As use owning loaders/serializers | Parity | Historical incompatibility remains explicit; no silent migration. |
| Immutable fork/revision semantics | Existing concrete Workbench fork APIs | Parity | Canonical B3 radius-2 fork remains the only one-click B3 sensitivity fork. |
| Semantic diff | Existing Workbench diff contracts rendered natively | Parity | No desktop diff engine. |
| Controlled Simulation authoring | Stable WB semantic slots | Parity | Explicit/derived/frozen meaning remains separate. |
| Reference Ecology Guided/Advanced authoring | Existing WB4 metadata/applicability/normalization | Parity | Unsupported Expert/extension composition remains absent. |
| Evidence authoring and advisories | Existing concrete evidence-plan contracts | Parity | Missing evidence is never reconstructed after a run. |
| E3/E4 Experiment authoring | Existing concrete definitions/expansion | Parity | Factor, replicate, arm, and counterbalance semantics remain distinct. |
| Curated B3 design | Read-only compiled design plus supported radius-2 fork | Parity | Derived fork loses canonical validated identity. |
| Readiness and diagnostics | Existing Workbench readiness/remediation | Parity | Desktop does not duplicate scientific preflight. |
| Run Plan | Exact bound owner reviewed before execution | Improvement | Native flow binds pending science atomically before execution. |
| Scientific execution | Existing concrete runners via Qt worker | Improvement | GUI stays responsive; runner/science semantics are unchanged. |
| Results across all five families | Existing WB5 inspectors and authoritative values | Parity | No universal result hierarchy. |
| Historical run provenance limitation | Explicitly reported | Parity | Reopening a Study does not synthesize absent result payloads. |
| Reference Ecology world replay | `WorldPresentationFrame` rendered in Qt Quick | Improvement | Plotly/browser renderer is no longer required by the product. |
| B3 matched world replay | Native paired control/treatment world at common seed/step | Improvement | Science-owned fixed encoding and matched-by-seed language are preserved. |
| Playback, selection, labels, trails, Focus Mode | Native presentation controls | Improvement | Keyboard commands are available; state remains presentation-only. |
| B3 Scientific Story eligibility | Existing `prepare_b3_workbench_cinematic()` | Parity | Canonical story eligibility remains science-owned. |
| Optional renderer availability | Reported separately from story eligibility | Parity | Missing Manim does not make the validated scientific handoff disappear. |
| B3 cinematic rendering | Existing director/renderer on a Qt worker | Improvement | Expensive rendering does not block the GUI. |
| Cinematic quality/output | Native transient controls | Parity | Values are never written to Study identity or manifests. |
| Cinematic output consumption | Save to file and open with the desktop OS | Intentional product difference | Native Q5 does not add Qt Multimedia solely to reproduce Streamlit inline video. |
| Application menus/shortcuts | Native File/Study/Presentation commands | Improvement | New/Open/Save/Save As/Run/Home/Back/Focus/playback have desktop commands. |
| Accessibility and responsive layout | Native focus order, accessible names, contrast/state cues, resize hardening | Improvement | Automated checks supplement but do not replace human accessibility audit. |
| Browser-specific session/download behavior | Replaced by native application/file state | Intentionally dropped | It is not a scientific or Workbench contract. |

## What is not a parity requirement

The older pre-Workbench dashboard and generic portfolio surfaces are not Q5 product
requirements merely because they still exist under `evo_engine.ui`. WU1–WU5 define
the migration reference. Q5 does not preserve browser-specific widget behavior,
Plotly-specific choreography, Streamlit session mechanics, or an inline media player
when a native desktop equivalent is sufficient.

Likewise, installer/signing/notarization, auto-update, 3D rendering, a plugin system,
and new biology remain outside Q5.

## Deprecation policy

From Q5 onward:

1. Product work targets `evo_engine.desktop` and shared frontend-neutral contracts.
2. `evo_engine.ui` receives only compatibility/security/build fixes needed while it
   remains in the repository; it receives no new product features.
3. New scientific capability continues to be implemented in Workbench/domain layers,
   never exclusively in Qt, so deprecating Streamlit does not move scientific truth
   into the frontend.
4. Tests may continue to exercise Streamlit-derived shared contracts during the
   retirement window where they provide useful regression evidence.
5. Physical Streamlit/Plotly removal should be a bounded maintenance change after a
   human native release audit confirms the replacement product on supported desktop
   hardware.

## Release-audit boundary

Q5 CI can prove typing/lint, controller behavior, QML loading, offscreen workflow
coverage, renderer-neutral invariants, standalone build, and packaged launch. It
cannot honestly prove human keyboard navigation, screen-reader behavior, OS font
scaling, perceived contrast, live resize ergonomics, or the subjective quality of a
full rendered B3 film. Those checks remain the explicit human release-audit gate; the
Streamlit deprecation decision does not convert automated evidence into a claim that
that audit occurred.
