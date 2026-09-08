# 0010 — Use PySide6 and Qt Quick for the primary Workbench frontend

- **Status:** Accepted
- **Date:** 2026-09-08
- **Supersedes:** —
- **Superseded by:** —

## Context

WU1–WU5 used Streamlit to establish the Workbench product model quickly while the
scientific architecture was still being pressure-tested. That sequence proved the
persistent Study shell, concrete Study-family routing, immutable revision/fork
semantics, readiness and Run Plan behavior, exact execution/result ownership,
family-specific Results, recorded-state world replay, and the B3 cinematic handoff.
Streamlit was therefore a useful reference frontend for settling product semantics.

The intended end product is also a downloadable desktop application with richer
native interaction and presentation. Q0 tested whether PySide6 with Qt Quick/QML
could provide that product surface without introducing a second scientific model,
a Qt-specific Study schema, IPC, a second backend, or renderer-owned science.

The Q0 Reference Ecology vertical demonstrated the full boundary:

```text
Qt Quick / QML
        ↓
PySide6 QObject controller + Qt item models
        ↓
existing Workbench semantics and exact persistence
        ↓
existing experiments / presets / presentation adapters
        ↓
biology
        ↓
frozen kernel
```

The vertical creates or opens an existing `ReferenceStudyRevision`, exposes one
semantic authoring choice, shows explicit and derived meaning from the existing
Workbench recipe, creates an immutable child revision through the existing fork API,
runs the exact revision outside the GUI thread, reads an authoritative Results value,
prepares the existing renderer-neutral `WorldPresentationFrame`, and renders that
frame natively in QML. A standalone executable is built with the Qt for Python
deployment tooling and launch-smoked in CI.

## Decision

PySide6 + Qt Quick/QML is the primary product frontend architecture for the Evolution
Experiment Workbench.

The scientific authority does not move into Qt. The durable dependency direction is:

```text
QML presentation/application state
        ↓
curated Qt properties / signals / slots / item-model roles
        ↓
Python controller/application orchestration
        ↓
existing concrete Workbench APIs
        ↓
existing scientific composition and validation
```

QML must not receive arbitrary mutable Workbench/domain object graphs. Scientific
changes must continue through the concrete Workbench authoring/fork APIs, and exact
saved artifacts remain the existing concrete Workbench JSON formats. There is no
Qt-specific Study schema or generic frontend schema.

`WorldPresentationFrame` remains the renderer-neutral native-world input. Qt must not
reconstruct spatial evidence or use Plotly figures as a new scientific contract.
Renderer selection, layout, highlighting, animation, and other display state remain
downstream presentation concerns.

Existing synchronous Workbench runners may execute through a narrow Qt worker so the
GUI thread remains responsive. Q0 does not establish a generic job system,
cancellation model, multiprocessing layer, or distributed execution architecture.

PySide6 remains an optional application dependency rather than a dependency of the
core simulation engine. Qt-specific type, QML-load, launch, and packaging checks live
in the dedicated desktop validation surface; lower packages must not depend on
`evo_engine.desktop` or PySide6.

Streamlit remains temporarily as the reference frontend during migration. Its
settled WU1–WU5 behavior is a compatibility target and a source of proven product
semantics, not a second scientific authority. Removal is a future explicit decision
after native parity makes the reference frontend unnecessary.

## Alternatives considered

### Keep Streamlit as the final product frontend

This would preserve the fastest development path and the already-proven reference
application, but it does not provide the desired native downloadable application
architecture or the same control over desktop interaction and rendering. Streamlit
remains valuable as a reference during migration rather than the primary final
surface.

### Electron or Tauri

Both could provide downloadable desktop shells, but they would add a web/runtime
boundary and, for the current Python scientific stack, pressure toward IPC or another
integration layer. Q0 showed that Qt can call the existing Python Workbench directly,
so that additional boundary is not currently earned.

### A game engine

A game engine could provide richer real-time graphics, but it would introduce a much
larger runtime and a second application ecosystem before the project has evidence
that native 3D or game-engine rendering is required. The current renderer-neutral
presentation contracts already support the needed 2D scientific world proof.

### A custom C++ renderer/application

This would maximize native control but would prematurely duplicate application
infrastructure and cross the Python scientific boundary without measured need. A
native execution backend remains evidence-driven future work.

## Consequences

- New product UI work should normally target `evo_engine.desktop` and Qt Quick/QML.
- Q-series milestones expand native product breadth by consuming existing concrete
  Workbench contracts; they do not redesign Workbench to simplify Qt.
- Shared frontend-neutral helpers should be extracted only when two real consumers
  demonstrate the same responsibility.
- Streamlit remains green and usable during migration but is no longer the primary
  product-development direction.
- Desktop packaging is now an explicit application concern. Q0 proves one-platform
  standalone deployment only; signed installers and a Windows/Linux/macOS release
  matrix remain later work.
- Qt remains downstream of scientific meaning, and the frozen kernel is unaffected.

## References

- `docs/evolution_experiment_workbench.md`
- `docs/workbench_architecture_review.md`
- `docs/workbench_ui.md`
- `docs/desktop_workbench.md`
- `docs/architecture/scientific_visualization.md`
- ADR 0009
- GitHub Issue #197
- GitHub PR #198
