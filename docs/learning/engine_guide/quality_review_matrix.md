# Quality Review Matrix

Use this table for consequential changes. Fill it qualitatively; do not invent
numeric scores for readability or maintainability.

| Dimension | Before | After | Evidence / reasoning |
| --- | --- | --- | --- |
| correctness |  |  | focused tests |
| semantic contracts |  |  | authoritative docs / ADR |
| time complexity |  |  | scale-variable analysis |
| memory |  |  | size + lifetime / tracemalloc if needed |
| measured runtime |  |  | profile / benchmark |
| readability |  |  | control-flow/naming/cognitive load |
| maintainability |  |  | change radius / duplicate paths |
| extensibility |  |  | real axes of variation |
| testability |  |  | focused-test isolation |
| coupling/cohesion |  |  | dependency/responsibility review |

## Decision prompt

> Is the measured/scientific value of the change large enough to justify any new
> conceptual, maintenance, or semantic cost?
