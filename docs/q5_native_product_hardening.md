# Q5 Native Product Hardening and Accessibility

Q5 hardens the existing PySide6 + Qt Quick Evolution Experiment Workbench after Q4.
It is downstream product work: scientific ownership remains in the existing Workbench,
experiment, evidence, and renderer-neutral presentation contracts.

## Scope

Q5 focuses on clean QML runtime behavior, keyboard/focus semantics, accessibility,
responsive layout, readable native Presentation defaults, coherent workflow/error
states, and end-to-end native product verification.

The settled dependency direction remains:

```text
Qt Quick / QML
        ↓
curated PySide6 QObject controllers + Qt item models
        ↓
existing Workbench/application semantics
        ↓
experiments / presets / renderer-neutral presentation
        ↓
biology
        ↓
frozen kernel
```

For scientific-world Presentation, `WorldPresentationFrame` remains the authoritative
renderer-neutral frame contract. Q5 does not create another replay/scientific frame,
change scientific encodings from screen density, or reconstruct missing evidence.

## Stable native conventions

### Runtime and component ownership

Dynamic route/section components receive their theme and controller dependencies
explicitly through the root shell. Delegate-local values are addressed through
explicit delegate IDs rather than relying on ambiguous dynamic QML scope. Desktop CI
loads the shell, walks all five native authoring families/sections, and treats
unexpected QML warnings as failures rather than suppressing them globally.

### Keyboard and focus

Primary interactive controls opt into tab focus and use visible focus outlines.
Sidebar section navigation has deliberate vertical key navigation, major route and
section replacement transfers focus into the live replacement content, and the exact
Run Plan takes focus when opened. Scientific-world organisms are keyboard-focusable;
Enter, Return, or Space selects the focused organism for the existing committed-value
inspector.

### Accessibility semantics

Buttons, disclosure controls, diagnostics, badges, scientific worlds, organisms,
resources, carcasses, trails, and inspectors expose meaningful accessible names,
roles, descriptions, and selected/checked state where applicable. Important product
and scientific distinctions are reinforced by text, outline/shape, and inspector
content rather than hue alone. In particular, organism selection is represented by a
gold halo/outline plus explicit selected/inspector semantics.

These semantics remain presentation-only and do not alter scientific encoding or
Workbench readiness meaning.

### Presentation density

Labels and trails now default **off** for both fresh and reset Presentation state.
They remain explicit user-controlled renderer choices. This is intentionally not a
population-density heuristic: every organism and committed scientific value remains
present, no evidence is aggregated or hidden, and the fixed science-owned focal-trait
encoding is unchanged.

The dense renderer proof deliberately enables labels/trails as a stress case. It may
look crowded at high population sizes; that visual pressure is not permission to
change scientific meaning silently.

### Responsive layout

The native shell has a minimum useful window of 1024 × 700, bounded sidebar widths,
wrapping study/header text, multi-column layouts that collapse at narrower widths,
scrollable authoring/results content, and world legend/inspector layouts that collapse
from two columns to one when space is constrained. Matched B3 retains symmetric
control/treatment emphasis rather than privileging one arm during layout pressure.

## Representative product verification

Automated native product tests exercise product transitions rather than recalculate
science in QML:

- Reference Ecology: create → semantic edit → immutable child binding → Run Plan →
  off-GUI-thread execution handoff → owned Results → committed Presentation replay;
- canonical B3: create → Run Plan → execution handoff → matched confirmation seed and
  committed-step replay → arm-local organism inspection;
- E3: editable experiment definition → exact bound definition → Run Plan → execution
  handoff → Results ownership;
- blocked E4: invalid empty seed draft remains blocked, cannot open a Run Plan, and
  surfaces actionable native status.

Focused QML tests additionally cover warning-free shell/family/section loading and
focus transfer after dynamic route replacement.

The current candidate's Desktop workflow also passes source Qt Quick launch, the Q4
offscreen renderer measurement/visual-proof run, standalone application build, and
packaged executable launch smoke. The captured dense Reference and matched-B3 renders
were inspected from CI artifacts: product hierarchy and matched-arm symmetry remain
coherent; the deliberately labels+trails-on dense Reference stress render is crowded,
as expected, while the ordinary default remains labels/trails off.

## Manual-verification boundary

This execution environment cannot perform a genuine human keyboard-only desktop
session, screen-reader session, operating-system font-scaling audit, or hardware
window-resize session. Offscreen Qt automation and rendered CI artifacts provide
strong supplementary evidence, but they are not represented as equivalent to that
manual release-quality audit. A later release-readiness pass should repeat the
keyboard/focus, assistive-technology, scaling, and representative-window checks on an
interactive desktop.

## Remaining product / release debt

This hardening slice intentionally leaves several concerns for the subsequent native
integration/release work:

- canonical B3 cinematic rendering/playback is not yet integrated into the native
  shell;
- the native-vs-Streamlit parity matrix and explicit Streamlit retirement decision
  are not made here;
- application-wide Run/Home/Focus/playback shortcut coverage is not yet complete;
- installer/signing/notarization, auto-update, release channels, and a broad platform
  matrix remain out of scope;
- true interactive accessibility/manual release verification remains required.

Streamlit therefore remains a compatibility/reference frontend at this checkpoint.
Those deferred items must not be mistaken for missing scientific architecture: the
native shell, authoring, execution, Results, and committed scientific-world contracts
continue to use the same authoritative Workbench/science layers.
