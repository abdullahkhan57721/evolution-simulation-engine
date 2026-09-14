# Current Project State

This page is a concise orientation snapshot for contributors and AI agents. It
answers **where the project is now** without replacing live repository state.

## Authority and staleness boundary

When anything here disagrees with the repository, use this order:

1. current `main`, tests, and CI;
2. root `AGENTS.md`;
3. authoritative architecture/subsystem documentation and ADRs;
4. active GitHub Issues and PR recovery checkpoints;
5. this orientation snapshot;
6. conversation history.

Do not store volatile commit SHAs, CI state, or detailed ticket progress here.

## Architectural baseline

The repository retains a frozen domain-neutral transactional kernel with general
evolution and biological specialization above it:

```text
validation / context / generic foundations
                    ↓
             simulation kernel
                    ↓
         general evolution abstractions
                    ↓
      biological/domain specializations
                    ↓
        processes and resolvers
                    ↓
       presets / experiments / interfaces
```

The kernel is in maintenance mode. New modeled behavior normally belongs above it
unless a genuine generic deficiency is demonstrated.

Scientific evidence and presentation remain downstream:

```text
modeled system
        ↓
committed state / committed events
        ↓
pure scientific measurement
        ↓
replicate outcome / treatment comparison
        ↓
renderer-neutral scientific meaning
        ↓
interactive / cinematic presentation
```

Presentation interpolation, camera behavior, layout, renderer settings, and desktop
preferences are never scientific evidence or scientific identity.

## Settled modeled and scientific capabilities

Biological specialization owns concrete genetics, inheritance, development, life
history, growth, energetics, feeding, movement, predation, reproduction, spatial
ecology, and biological world state above domain-neutral contracts.

Reproduction distinguishes participants, investors, genetic contributors, and
production sources. Chromosome transmission separates copy structure, pairing,
recombination, segregation, and gamete formation. Current Mendelian/diploid policies
remain concrete policies rather than universal architecture rules.

Committed evidence is first-class: population and spatial observations, selected
individual trait records, allele/genotype composition, pedigree/life-history data,
causal event/effect telemetry, deterministic seeded execution, checkpoint/resume,
and reproducible multi-seed experiments are established capabilities.

### Controlled science: E1–E7

E1–E7 form the completed first controlled experimental-evolution sequence:

```text
E1 measurement/reproducibility
 → E2 controlled locomotion
 → E3 performance landscape
 → E4 selection on standing variation
 → E5 finite-population drift/weak selection
 → E6 rare-lineage invasion/candidate stability
 → E7 mutation-driven accessibility
```

A run/seed is the current experimental replicate; organisms inside a run are dependent
observations. Event step `t` aligns with committed state `t + 1`. Extinction,
censoring, discovery/confirmation roles, and representative storytelling remain
explicit. Scientific measurements consume committed evidence, and no universal
statistics DSL or kernel-owned scalar fitness abstraction exists.

E7's frozen confirmation is a meaningful negative result: the tested high-mutation
configuration does **not** show cross-start convergence. Do not retune or lengthen E7
post hoc to manufacture the expected story. Any follow-up requires a new scientific
identity and predeclared design.

### Confirmed B3 flagship

B3 is the richer integrated reference-ecology flagship. It compares matched uniform
renewable resources with compact radius-1 patches under balanced inherited
`max_speed = 1 / 4` standing variation. Independent confirmation, mechanism evidence,
founder-label counterbalancing, and a radius-2 sensitivity bound the claim.
Representative seed 5 and its committed episodes are selected by B3 science, not a
renderer.

Scenario origin and validated identity are distinct. The radius-2 sensitivity fork
keeps B3 origin but loses canonical radius-1 identity and cannot inherit the canonical
headline cinematic handoff.

## Evolution Experiment Workbench

WB1–WB6 establish the first stable Workbench architecture:

```text
semantic intent / curated scenario / concrete experiment definition
        ↓
bounded resolution
        ↓
immutable manifest / treatment specification
        ↓
existing typed/scenario composition + lower validation
        ↓
frozen kernel
        ↓
committed evidence + authoritative scientific results
        ↓
Study-facing Results
        ↓
downstream presentation
```

Durable contracts include:

- editable intent is separate from resolved immutable scientific meaning;
- stable scientific IDs do not depend on Python paths/object identity;
- exact load uses stored manifests rather than current defaults;
- incompatible exact reproduction fails explicitly rather than silently migrating;
- mutable runtime/recorder/spec objects are reconstructed fresh;
- EvidencePlan remains separate from simulation intent;
- runs retain exact revision/manifest/evidence/provenance identity;
- forks create immutable children with lineage;
- scenario origin is distinct from validated scenario identity;
- factor, treatment, counterbalance/blocking, replicate, and measurement remain
  distinct concepts;
- missing evidence makes analysis/presentation unavailable rather than inferable;
- scientific encodings remain renderer-neutral;
- presentation choices never alter scientific manifests.

`Study / Simulation / Evidence / Experiment / Results / Presentation` is a product
navigation model, not a required universal class hierarchy. `Run` is an action.
Workbench diagnostics remain bounded and do not replace lower generic, biological,
genetic, or simulation preflight.

The official support envelope remains deliberately narrower than engine capability:

```text
engine-valid ≠ Workbench-supported ≠ Guided ≠ experiment factor levels
```

Controlled locomotion, canonical/derived B3, E3, E4, and bounded Reference Ecology are
the current concrete Workbench families. Reference Ecology has Guided and Advanced
supported authoring; Expert is intentionally empty and Extension/Internal remains
non-product composition capability.

## Native desktop Workbench: Q0–Q5

PySide6 + Qt Quick/QML is the primary product architecture. Scientific authority
remains in Workbench/domain layers:

```text
Qt Quick / QML
        ↓
PySide6 QObject controllers + explicit Qt item models
        ↓
existing Workbench/application semantics
        ↓
experiments / presets / renderer-neutral presentation
        ↓
biology
        ↓
frozen kernel
```

Q0 proved the technology/deployment boundary. Q1 established Home/New/Open plus the
persistent five-section Study shell and exact concrete routing. Q2 completed supported
Simulation/Evidence/Experiment authoring. Q3 completed reviewable Run Plans,
five-family off-GUI-thread execution, and authoritative family-specific Results. Q4
made `WorldPresentationFrame` the native interactive scientific-world contract for
Reference Ecology and canonical matched B3.

Q5 hardens those settled seams rather than redesigning them. The native product now
owns responsive desktop composition, accessibility/focus semantics, native commands,
end-to-end workflow polish, and the B3 cinematic handoff. Cinematic science remains:

```text
B3 revision + authoritative result
        ↓
prepare_b3_workbench_cinematic()
        ↓
existing B3 director plan
        ↓
optional renderer
```

Scientific story eligibility is distinct from optional Manim availability. Expensive
rendering runs outside the Qt GUI thread. Quality, output format/location, replay,
focus, labels, trails, and other view state are presentation-only. A radius-2 B3 fork
cannot claim canonical headline-cinematic eligibility.

Native application commands cover New, Open, Save, Save As, Run, Home/back, Focus
Mode, and committed-step playback. Exact scientific ownership remains atomic: owner
replacement clears stale result/run-plan/presentation state, while navigation alone
cannot mutate science.

### Frontend decision

Q5 completes the WU1–WU5 parity review. **The native Qt application is the sole
product frontend. The sophisticated Streamlit Workbench is deprecated.** Existing
`evo_engine.ui` code is temporarily retained as frozen regression/reference material;
it receives no new product features and future milestones do not owe it parity.
Physical removal should follow a human native release audit and an explicit check that
remaining compatibility value can be discarded.

See `docs/development/q5_frontend_parity.md`, `docs/desktop_workbench.md`,
`docs/q4_native_presentation.md`, and ADR 0010.

## Results and presentation boundary

Results navigation is concrete presentation over authoritative artifacts and existing
scientific measurements; it does not recalculate E1/E3/E4/B3 science. If required
evidence was not recorded, a new run with the appropriate EvidencePlan is required.
Historical run references are not a durable observations/result archive and never
trigger implicit reruns.

Presentation remains downstream:

```text
model / evidence / experiments
        ↓
     Workbench
        ↓
   +----+----+
   |         |
   v         v
native UI  cinematic
```

`WorldPresentationFrame` remains the authoritative renderer-neutral world contract.
QML receives curated scalar properties/signals/slots/item-model roles rather than
arbitrary Workbench/domain object graphs. Exact committed frames are evidence;
adjacent stable-identity interpolation is display-only.

## Current development front

The Workbench foundation, E1–E7 controlled sequence, confirmed B3 flagship,
WU1–WU5 reference sequence, and Q0–Q5 native product sequence are established.
Q5 closes the frontend migration decision: Qt is the product; Streamlit is deprecated
reference code.

The next work should be chosen from concrete need rather than continuing UI migration
by inertia:

1. **Human native release audit:** actually exercise keyboard navigation, focus order,
   OS font scaling, contrast/color-vision legibility, live resize, representative
   long Results, Reference custom authoring, E3/E4, canonical B3, radius-2 B3, missing
   evidence, exact save/reopen, paired replay, and a real B3 film when Manim is
   installed. Automated offscreen CI does not satisfy this gate.
2. **Distribution only when required:** signing, notarization, installers, auto-update,
   and broader platform release proof should follow a real shipping requirement.
3. **New science/modeling only from a new question:** E7 does not imply an automatic
   E8. Potential fronts include generational accessibility, richer genetics,
   chromosome pairing/recombination, mating systems, development/G×E, and richer
   evolutionary ecology.
4. **Performance/backend work only from evidence:** no C++/OpenGL/shader/custom-scene
   renderer or Rust/C++ execution backend is justified without profiling and a stable
   target subset.

## Known architectural friction

Concrete persistence remains intentional: existing families have different ownership
responsibilities, and Q0–Q5 did not earn a universal saved Study/Experiment/Results
root. Workbench diagnostics remain bounded rather than a generic validation system.
Presentation bundles remain purpose-specific; do not turn the B3 director into a
camera/storyboard DSL without multiple real consumers.

The native product is broad and automated validation is substantial, but a real human
release-quality desktop/accessibility audit is still distinct evidence. Do not turn
headless QML loading, screenshot proof, or packaged launch smoke into a claim that the
human audit occurred.

The scientific scope remains illustrative: Reference Ecology, B3, and E2–E7 are
software/modeling demonstrations, not calibrated predictions about real species.

## Collaboration and validation

Use ChatGPT primarily for architecture, roadmap sequencing, consequential contracts,
tightly scoped sequential implementation, and independent PR review/merge decisions.
Use Codex selectively for execution-heavy work behind settled interfaces.

For substantial work follow:

```text
Issue → branch → implementation → early PR → focused validation
      → exact-head CI/review → squash merge → main verification
```

Use `docs/development/validation_workflow.md` for the layered validation policy.
Repository truth always wins over this summary.
