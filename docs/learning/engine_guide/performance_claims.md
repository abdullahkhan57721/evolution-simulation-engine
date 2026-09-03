# How to State Performance Claims Carefully

Performance claims are easy to overstate. Use this vocabulary throughout the
textbook and project work.

## Strongly preferred claim forms

```text
Algorithmic:
    "This loop adds O(R) kernel-side iteration over accepted events."

Parameterized:
    "Total cost also includes resolver and process-specific work."

Measured:
    "In the fixed synthetic kernel workload, profiling identified X as a major
    cumulative path."

Historical:
    "A previous optimization campaign removed repeated per-event dispatch work."

Uncertain:
    "This may become a scaling hazard at larger N; profile a representative
    workload before implementation tuning."
```

## Avoid

```text
"This function is fast."
"This engine is O(n)."
"Dictionary lookup makes this optimal."
"This change improves performance" without comparable measurements.
"This is the bottleneck" based only on code appearance.
```

## Layer attribution

Always distinguish:

```text
kernel orchestration cost
domain process cost
observation cost
experiment/export cost
```

A reference-simulation hotspot is not automatically a kernel hotspot.

## Timing values

Machine-dependent milliseconds are evidence for a measured environment, not
permanent architectural facts. Prefer stable lessons and structural call/work
changes in pedagogical prose; link to authoritative performance docs for current
measurements.
