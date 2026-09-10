from pathlib import Path


def replace_section(text: str, start: str, end: str, replacement: str) -> str:
    start_index = text.index(start)
    end_index = text.index(end, start_index)
    return text[:start_index] + replacement + text[end_index:]


# Native desktop architecture handoff.
desktop_path = Path("docs/desktop_workbench.md")
desktop = desktop_path.read_text(encoding="utf-8")
desktop = desktop.replace(
    "Q0 establishes **PySide6 + Qt Quick/QML** as the primary product frontend architecture\nfor the Evolution Experiment Workbench. Q1 establishes the persistent native Study\nshell and concrete routing; Q2 completes the currently supported pre-execution\nSimulation/Evidence/Experiment authoring surface. The Streamlit WU1–WU5 application\nremains a reference frontend during migration; it does not become a second scientific\nmodel.\n",
    "Q0 establishes **PySide6 + Qt Quick/QML** as the primary product frontend architecture\nfor the Evolution Experiment Workbench. Q1 establishes the persistent native Study\nshell and concrete routing; Q2 completes the supported pre-execution\nSimulation/Evidence/Experiment authoring surface; Q3 completes native Run planning,\nfive-family execution, and authoritative Results breadth. The Streamlit WU1–WU5\napplication remains a reference frontend during migration; it does not become a\nsecond scientific model.\n",
)
desktop_q3 = '''## Q3 native execution and Results

Q3 completes the first native `Run → Results` breadth across all five supported
concrete Study families without creating a common scientific result hierarchy.

`ApplicationController` binds pending scientific state to one exact immutable owner
before Run Plan review. Controlled and Reference Simulation/Evidence drafts therefore
produce one child revision containing the complete pending scientific state rather
than a chain of intermediate revisions. Pending E3/E4 experiment edits become the
exact immutable experiment definition. B3 remains its exact curated revision.

`RunController` owns only transient native execution coordination:

```text
exact active scientific owner
        ↓
reviewable Run Plan
        ↓
QThread worker
        ↓
frontend-neutral Workbench execution dispatcher
        ↓
existing concrete runner
        ↓
authoritative result + provenance
```

The Workbench execution dispatcher is shared by Streamlit and Qt only because the
second real frontend earned that extraction. It still dispatches explicitly to the
five existing concrete runners. The Qt adapter adds no generic queue, cancellation,
progress, multiprocessing, or background-job protocol.

Completion is accepted only while the same exact scientific owner remains active and
the existing WB5 association rules accept the returned result. Scientific edits,
owner replacement, or Home navigation invalidate stale Run Plans, Results, and
presentation ownership.

`ResultsController` is intentionally family-dispatched. Controlled, Reference, E3,
E4, and B3 Results all use the familiar `Overview / Explore / Analysis / Provenance`
product rhythm while preserving their different scientific structures:

- controlled Results expose recorded population plus existing E1 locomotion
  measurements only when their evidence exists;
- Reference Results expose independent availability for population, committed events,
  pedigree, genetics, and spatial replay;
- E3 preserves maximum speed as factor plus factor-level, seed, treatment, and
  manifest identity;
- E4 preserves resource geography as factor while keeping control/treatment role,
  seed, standing focal composition, and founder-order counterbalance distinct;
- B3 preserves scenario origin versus validated scenario identity and keeps primary
  confirmation, radius sensitivity, and founder counterbalance separate.

Missing evidence stays visibly unavailable and requires a new run with an appropriate
EvidencePlan. Native Reference world rendering remains contingent on actual recorded
spatial observations. Persisted run provenance remains a reference to a historical
run, not a persisted observations/result archive, so reopened Studies never
reconstruct or implicitly rerun historical Results.

### Q4 Presentation handoff

Q4 should now broaden native Presentation from the exact current-session evidence and
result ownership settled by Q3. Begin with the existing renderer-neutral Reference
world path and canonical B3 matched-presentation/cinematic contracts. Preserve
committed-step semantics, science-owned encodings, matched-arm identity, and
presentation-only interaction state.

Do not infer a universal scene/camera/replay model, generic chart framework, or
cross-family presentation schema from Q3. Shared presentation helpers should be
promoted only when multiple concrete native consumers demonstrate the same
responsibility. Accessibility, visual completion, installer/signing/update work, and
the final Streamlit parity/removal decision remain later product-hardening work.

'''
desktop = replace_section(
    desktop,
    "## Q3 execution / Results handoff\n",
    "## References\n",
    desktop_q3,
)
desktop = desktop.replace(
    "- GitHub Issue #203 / PR #204\n",
    "- GitHub Issue #203 / PR #204\n- GitHub Issue #205 / PR #206\n",
)
desktop_path.write_text(desktop, encoding="utf-8")


# Rolling roadmap: Q3 is completed capability; Q4 becomes the front.
roadmap_path = Path("docs/development/roadmap.md")
roadmap = roadmap_path.read_text(encoding="utf-8")
roadmap_q3_q4 = '''### Q3 — execution and Results breadth (completed)

Q3 broadens native execution and Results across the existing five-family Workbench
support envelope while keeping scientific authority in existing runners and WB5
inspectors. It establishes atomic pre-run binding to exact immutable scientific
ownership, reviewable native Run Plans, one narrow off-GUI-thread execution adapter,
exact provenance/result association, family-specific native Results, explicit missing
evidence, and honest historical-provenance behavior.

The shared execution dispatcher is frontend-neutral because Streamlit and Qt are now
two real consumers; it remains an explicit five-family dispatcher rather than a job
or workflow framework. Results remain heterogeneous by design rather than being
flattened into a universal statistics/result model.

### Q4 — native Presentation breadth

Q4 should extend Presentation from recorded evidence now that native Run and Results
ownership are settled. Start with broader Reference world exploration and canonical
B3 matched replay plus the existing cinematic handoff. Reuse existing renderer-neutral
scientific encoding and presentation adapters; do not infer a universal scene,
camera, playback, or chart schema.

Q4 must preserve exact Study/run/treatment/replicate identity, committed-step
semantics, shared science-owned trait scales, and the fact that matched B3 arms are
independent stochastic executions after treatment-driven divergence. Presentation
interaction state remains downstream and cannot change scientific identity.

### Later native product direction

After sufficient Presentation breadth, apply accessibility, visual completion,
packaging/release hardening, and an explicit Streamlit parity/removal decision to the
native application. Signing, notarization, installers, auto-update, and a broader
platform release matrix should be added from concrete distribution requirements, not
predeclared as a generic application framework.

'''
roadmap = replace_section(
    roadmap,
    "### Q3 — execution and Results breadth\n",
    "The Q-series does **not** authorize:\n",
    roadmap_q3_q4 + "The Q-series does **not** authorize:\n",
)
roadmap_path.write_text(roadmap, encoding="utf-8")


# Concise current-state orientation.
state_path = Path("docs/development/current_state.md")
state = state_path.read_text(encoding="utf-8")
state = state.replace(
    "Q0 established that PySide6 + Qt Quick/QML can consume the settled Workbench\ndirectly. Q1 turned that technology proof into the persistent native product shell,\nand Q2 completes the first native pre-execution scientific authoring surface across\nSimulation, Evidence, and Experiment. Scientific authority remains in the existing\nWorkbench artifacts. The durable dependency boundary is:\n",
    "Q0 established that PySide6 + Qt Quick/QML can consume the settled Workbench\ndirectly. Q1 turned that technology proof into the persistent native product shell,\nQ2 completed the pre-execution Simulation/Evidence/Experiment authoring surface, and\nQ3 completes native Run planning, five-family execution, and authoritative Results\nbreadth. Scientific authority remains in the existing Workbench artifacts. The\ndurable dependency boundary is:\n",
)
state = state.replace(
    "current-session result, Run Plan placeholder, presentation-owner/reset, file, and\nstatus state.",
    "current-session exact result ownership, reviewable Run Plan coordination,\npresentation-owner/reset, file, and status state.",
)
q3_state = '''Q3 adds sibling `RunController` and `ResultsController` seams rather than turning
`ApplicationController` into a scientific workflow object. Pending controlled and
Reference Simulation/Evidence drafts are bound atomically to one immutable child
revision before Run Plan review; pending E3/E4 edits bind to their exact immutable
experiment definitions. A frontend-neutral Workbench dispatcher invokes only the
five existing concrete runners, while one narrow Qt worker keeps all five synchronous
execution paths off the GUI thread.

Completed results are accepted only when existing exact-owner/WB5 association rules
still match the active science. Native Results remain family-specific: controlled
population/locomotion, Reference evidence availability, E3 factor/seed/treatment/
manifest identity, E4 factor/role/standing-composition/counterbalance identity, and
B3 scenario/confirmation/sensitivity/counterbalance identity remain distinct. Missing
evidence stays unavailable; reopened historical run provenance is never treated as a
persisted observations archive or implicit rerun source. Reference world rendering
still requires recorded spatial evidence.

'''
state = state.replace(
    "The QML boundary remains intentionally curated:",
    q3_state + "The QML boundary remains intentionally curated:",
)
state = state.replace(
    "Existing\nsynchronous Reference execution is adapted through a narrow `QThread`; no generic\njob/cancellation framework has been earned.",
    "Q3 adapts all five existing synchronous Workbench runners through one narrow\n`QThread` execution seam; no generic job/cancellation framework has been earned.",
)
state = state.replace("WU2–WU5 and Q0–Q2 promote no capability", "WU2–WU5 and Q0–Q3 promote no capability")
state = state.replace(
    "Historical run references alone never become native replay data.",
    "Q3 extends that exact-owner gate across all five native Run/Results paths.\nHistorical run references alone never become native replay data.",
)
current_front = '''## Current development front

The Workbench foundation, E1–E7 controlled-science sequence, end-to-end Streamlit
reference product, and **Q0–Q3 native application sequence** are established.
PySide6 + Qt Quick/QML remains the primary product architecture without moving
scientific authority out of Workbench.

Q1 established the persistent native five-section Study shell and exact concrete
routing/persistence. Q2 completed supported Simulation/Evidence/Experiment authoring.
Q3 now completes the first native `Run → Results` breadth: exact atomic pre-run
ownership, reviewable Run Plans, off-GUI-thread execution for all five supported
families, WB5-authoritative family-specific Results, explicit missing evidence, and
honest historical-provenance semantics.

The next native product work should extend those settled seams rather than redesign
them:

1. **Q4 — native Presentation breadth:** expand recorded-evidence presentation,
   beginning with broader Reference world exploration and canonical B3 matched replay
   plus the existing cinematic handoff.
2. **Product hardening after functional breadth:** accessibility, visual completion,
   packaging/release hardening, and an explicit Streamlit parity/removal decision.
3. **Distribution work when concretely required:** signing, notarization, installers,
   auto-update, and broader platform release proof should follow real shipping needs.

Q4 must preserve exact owner/provenance, committed-step semantics, science-owned
encodings, and B3 matched-arm scientific identity without inventing a universal Qt
scene, replay, chart, or camera framework. Streamlit remains the semantic
reference/compatibility frontend until an explicit parity/removal decision.

E7 closes the current E1–E7 causal sequence with a confirmed negative convergence
result. Do not post-hoc lengthen, enrich, or retune E7 to manufacture convergence.
A future controlled-science milestone should begin from a new predeclared question
and new scientific identity. Potential pressure includes evolutionary accessibility
across longer generational turnover, richer reproduction/resource opportunity,
richer genetics, or changing ecology, but none of those is automatically the next
milestone merely because E7 exposed the mechanism.

Longer-term modeled fronts remain richer genetic expression, chromosome
pairing/recombination, mating systems, development/G×E, and evolutionary ecology.
A native Rust/C++ execution backend remains evidence-driven future work.

'''
state = replace_section(
    state,
    "## Current development front\n",
    "## Known architectural friction\n",
    current_front,
)
state = state.replace(
    "WB5/WB6, WU1–WU5, and Q0–Q2 still do not reveal enough identical persistence\nor execution responsibility to earn a universal saved Study/Experiment/Results root.\nQ1/Q2 reinforce the intended approach by routing and authoring concrete formats\ndirectly rather than manufacturing one for Qt.",
    "WB5/WB6, WU1–WU5, and Q0–Q3 still do not reveal enough identical persistence\nor result responsibility to earn a universal saved Study/Experiment/Results root.\nQ1–Q3 reinforce the intended approach by routing, authoring, executing, and\npresenting concrete families directly rather than manufacturing one for Qt.",
)
state = state.replace(
    "Q1 and Q2 establish the native shell, concrete five-family routing, exact\npersistence, application ownership semantics, and complete currently supported\npre-execution Simulation/Evidence/Experiment authoring. Reference Ecology still owns\nthe only deep native execution/result/world slice. Broader execution/Results,\nPresentation parity, accessibility, and release hardening remain Q3+ application\nwork. This is application-layer incompleteness, not a reason to broaden Workbench or\nthe kernel.",
    "Q1–Q3 establish the native shell, concrete five-family routing, exact persistence,\napplication ownership semantics, supported pre-execution authoring, reviewable Run\nPlans, five-family off-GUI-thread execution, and family-specific authoritative\nResults. Presentation breadth, accessibility, and release hardening remain Q4+\napplication work. This is application-layer incompleteness, not a reason to broaden\nWorkbench or the kernel.",
)
state_path.write_text(state, encoding="utf-8")


# Nav entry is staged before the final Q3 architecture note is created.
mkdocs_path = Path("mkdocs.yml")
mkdocs = mkdocs_path.read_text(encoding="utf-8")
mkdocs = mkdocs.replace(
    "      - Native Desktop Workbench: desktop_workbench.md\n",
    "      - Native Desktop Workbench: desktop_workbench.md\n      - Q3 Native Execution and Results: q3_native_execution_results.md\n",
)
mkdocs_path.write_text(mkdocs, encoding="utf-8")
