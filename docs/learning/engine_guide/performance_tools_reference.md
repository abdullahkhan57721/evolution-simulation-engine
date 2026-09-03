# Performance Tools Reference

This is a navigation aid, not a replacement for the authoritative
[Performance Measurement](../../performance.md) document.

## Complexity analysis

Use before running tools to identify scale variables and obvious hazards.

Question:

> How should cost grow as the model grows?

## `cProfile` / `pstats`

Use to identify cumulative/self runtime hotspots in a reproducible workload.

Repository entry points include:

```bash
venv/bin/python scripts/profile_kernel.py
venv/bin/python scripts/profile_reference.py
```

Use the kernel profiler for kernel-only claims; use reference profiles for
end-to-end/domain integration signals.

## `pyperf`

Use for statistically stronger focused before/after benchmarking once a small
operation has been identified as worth measuring.

Example repository benchmark:

```bash
venv/bin/python scripts/benchmark_state_copy.py
```

## `tracemalloc`

Use when Python allocation/peak traced memory is the unresolved question.

Example:

```bash
venv/bin/python scripts/benchmark_state_copy.py --tracemalloc
```

## Tool-selection rule

```text
scaling question         -> complexity analysis
where is time spent?     -> profiler
is this micro-change faster? -> benchmark
where are Python allocations? -> tracemalloc
```

Do not collect measurements merely because a tool exists. Start with a concrete
engineering question.
