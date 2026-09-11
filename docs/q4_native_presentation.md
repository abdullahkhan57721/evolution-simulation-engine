# Q4 Native Presentation and Q5 Handoff

Q4 replaces the Streamlit/Plotly interactive scientific world with a native Qt Quick
presentation surface while retaining the same renderer-neutral scientific authority.
It does **not** introduce a second replay model, a Qt-owned scientific schema, or a
new source of evidence.

## Authoritative pipeline

```text
committed evidence
        ↓
existing Workbench presentation adapters
        ↓
WorldPresentationFrame
        ↓
PresentationController
        ↓
explicit Qt item models
        ↓
Qt Quick / QML scientific world
```

`WorldPresentationFrame` remains the sole renderer-facing scientific frame contract.
The Qt layer may project its values into presentation-only models for binding and
render them, but it must not reconstruct observations, infer biology, or feed
interpolated values back into analysis.

## Scientific truth versus presentation

The native renderer preserves the distinction:

```text
recorded committed position / trait value = scientific evidence
interpolation between adjacent frames        = presentation only
```

Selecting or scrubbing to a committed step rebuilds the exact authoritative frame
for that step. Previous/next and playback advance through committed frame positions.
QML `Behavior` animation is permitted only for identity-stable organisms across
adjacent committed frames. Non-adjacent seeking, owner changes, births, deaths, and
other organism-set discontinuities reset delegates and snap to the authoritative
frame rather than drawing an invented continuous trajectory.

Labels, trail visibility, selection, Focus Mode, playback speed, and transition
timing are view state. They do not mutate the current `WorldPresentationFrame`, run
provenance, Study manifest, or analysis inputs.

## Native Reference Ecology replay

Reference Ecology consumes exactly the spatial evidence and Workbench adapter used by
WU5. The native surface provides:

- world bounds;
- organisms, resources, and carcasses when present in the frame;
- recorded recent movement trails;
- organism selection with a presentation-only halo;
- labels and inspector content;
- renderer-neutral focal-trait legend/encoding when a frame supplies one;
- committed-step timeline, previous/next, play/pause, and playback speed;
- Focus Mode as presentation state only.

Missing spatial evidence retains the existing Workbench availability/remediation
semantics. Qt does not synthesize a replay from population or event evidence.

## Native B3 matched replay

Canonical B3 replay is a scientific comparison, not two independently navigated
movies. `PresentationController` therefore maintains:

- one authoritative confirmation seed at a time;
- the intersection of committed steps available in both arms;
- one common selected committed step;
- independent control and treatment frame construction from their own recorded
  evidence;
- arm-local organism selection;
- identical renderer-neutral focal-trait encoding in both arms;
- explicit matched/blocked language.

The UI states that matching by seed and committed step does **not** imply RNG
lockstep once treatment-driven biology diverges. The shared `max_speed` encoding is
science-owned by the existing B3 Workbench presentation adapter, not chosen by QML.

## Qt presentation models

The desktop layer exposes explicit `QAbstractListModel` projections for organisms,
resources, carcasses, and movement trails. Roles contain only renderer-safe
presentation values from `WorldPresentationFrame` primitives. Arbitrary organism,
observation, experiment, or biology objects are not exposed to QML.

The organism model can preserve delegates only when the ordered organism identity set
is unchanged. That narrow optimization enables smooth adjacent-frame motion without
weakening discontinuity semantics.

## Visual grammar

The renderer preserves the established scientific channels:

- x/y position owns spatial location;
- focal scientific trait may own organism fill when the frame provides an encoding;
- selection uses a separate outline/halo channel;
- trails show recorded recent movement rather than interpolated evidence;
- labels and numeric inspector values provide non-hue reinforcement for critical
  scientific distinctions;
- renderer emphasis remains presentation state.

No 3D, terrain engine, game engine, camera DSL, generalized renderer framework,
custom C++ renderer, OpenGL backend, shader architecture, or scene-graph extension
was added.

## Validation and renderer evidence

Focused Desktop tests cover exact frame selection, adjacent-frame animation
eligibility, discontinuity resets, missing spatial evidence, view-state
non-scientific behavior, B3 common seed/step semantics, fixed focal encoding,
arm-local selection, and exact-owner reset.

Desktop CI also runs `scripts/q4_renderer_probe.py` under the pinned headless Qt
runtime. The probe launches the real native QML shell, drives canonical synthetic
`WorldPresentationFrame` values through the Q4 Presentation seam, captures Reference
and B3 screenshots, and records wall-clock projection plus Qt event-processing
measurements for:

- 64-organism Reference replay;
- 256-organism Reference replay;
- labels at 256 organisms;
- recorded trails at 256 organisms;
- an adjacent committed playback step;
- window resize;
- matched B3 replay with 128 organisms per arm.

The `q4-renderer-proof` Actions artifact contains `measurements.json`,
`reference-256.png`, and `b3-pair-128-per-arm.png`. These measurements are evidence
for optimization decisions, not benchmarks or scientific results. Q4 intentionally
adds no lower-level rendering technology unless measured behavior demonstrates a
need.

## Q5 integration boundary

Q5 can treat native scientific world replay as a settled desktop capability. Product
integration may improve navigation, accessibility, layout, cross-section flow,
visual polish, packaging, and release ergonomics while preserving these contracts:

1. `WorldPresentationFrame` remains the renderer-neutral frame authority.
2. Workbench adapters continue to own evidence-to-frame scientific meaning.
3. Qt models remain presentation-only projections.
4. Exact committed-step selection always reproduces authoritative frame values.
5. Animation never becomes evidence or analysis input.
6. Birth/death/appearance/disappearance and non-adjacent seeks remain visually
   honest discontinuities.
7. B3 keeps one shared seed/common step, independent arm frames, arm-local selection,
   fixed science-owned encoding, and no RNG-lockstep claim.
8. Missing evidence remains unavailable with remediation rather than reconstructed.
9. Performance changes require measurements before introducing lower-level native
   rendering machinery.

The retained Streamlit/Plotly implementation remains a behavioral compatibility
reference until the project makes an explicit parity/removal decision; it is not the
native renderer's scientific source of truth.
