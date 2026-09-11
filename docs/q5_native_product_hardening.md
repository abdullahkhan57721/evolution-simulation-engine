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
renderer-neutral frame contract. Q5 must not create another replay/scientific frame,
change scientific encodings from screen density, or reconstruct missing evidence.

## Implementation checkpoint

This document is created with the Q5 branch as an early recovery checkpoint. Stable
focus/accessibility conventions, presentation-density policy, release debt, and
native-versus-Streamlit parity gaps will be recorded here as the implementation is
completed.
