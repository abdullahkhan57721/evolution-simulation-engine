# Performance Measurement

Performance work follows a measurement-first rule: establish a reproducible workload, profile it, and optimize the measured hotspot before considering lower-level acceleration.

## Reference baselines

The engine defines two fixed performance scenarios using the default `ReferenceEcologyConfig` (`20` founders, `50` steps, seed `42`):

- **`reference-core`** builds the reference simulation and lifecycle without observers. It measures simulation execution and domain/process costs without observation overhead.
- **`reference-observed`** runs the same ecology through the complete reference observation and telemetry stack. Comparing it with the core scenario exposes the additional cost of observability.

Both scenarios time only `SimulationEngine.run(...)`. Configuration, object construction, and profiler/report serialization are deliberately outside the measured wall-clock interval.

Every warmup and measured repeat is built from fresh deterministic state. Repeated measured runs must finish with the same high-level outcome dimensions (completed steps, population size, carcass count, and total resources), otherwise the benchmark fails rather than comparing unlike executions.

## Run the profiler

From the repository root with the project virtual environment installed:

```bash
venv/bin/python scripts/profile_reference.py
```

Useful focused runs include:

```bash
venv/bin/python scripts/profile_reference.py --scenario core
venv/bin/python scripts/profile_reference.py --scenario observed
venv/bin/python scripts/profile_reference.py --scenario all --repeats 5 --warmups 2 --top 40
```

By default artifacts are written under `outputs/performance/`:

- `<scenario>-benchmark.json` — machine-readable wall-clock samples, summary statistics, environment metadata, configuration, and final outcome dimensions.
- `<scenario>-profile.txt` — human-readable functions ordered by cumulative profiler time.
- `<scenario>.prof` — raw `pstats` data for deeper inspection with standard Python profiling tools.

The console also prints the benchmark summary and top cumulative-time profile rows.

The GitHub Actions quality workflow runs both fixed scenarios as an informational performance check and uploads the same `outputs/performance/` files as a retained workflow artifact. This preserves the exact JSON, text profile, and raw `pstats` inputs used for later comparisons instead of relying only on console logs.

## Focused pyperf microbenchmarks

Use `pyperf` when a profile identifies a small operation that needs statistically stronger before/after measurement. Performance-only tooling is kept separate from the runtime package and normal development dependencies:

```bash
venv/bin/python -m pip install -r requirements-performance.txt
```

The state-copy benchmark exercises the fixed initial reference ecology:

```bash
venv/bin/python scripts/benchmark_state_copy.py -o outputs/performance/state-copy.json
```

For faster exploratory runs:

```bash
venv/bin/python scripts/benchmark_state_copy.py --fast
```

For two result files captured on comparable machines/environments, use pyperf's comparison tools rather than comparing a single timing sample:

```bash
venv/bin/python -m pyperf compare_to before.json after.json --table
```

`pyperf` calibrates benchmark loops, can use multiple worker processes, records environment metadata, and warns when results appear unstable. The CI performance job runs a fast pyperf copy benchmark as directional evidence; serious optimization decisions should still use repeated local measurements on a controlled machine.

## Allocation measurement

For Python-level copy/allocation hotspots, use `tracemalloc` before lower-level allocator instrumentation. The same pyperf benchmark can report traced peak memory rather than elapsed time:

```bash
venv/bin/python scripts/benchmark_state_copy.py \
  --tracemalloc \
  -o outputs/performance/state-copy-tracemalloc.json
```

This identifies the memory footprint of Python allocations made by the benchmarked copy operation and is appropriate when the suspected cost is object-graph construction, containers, tuples, or other Python-managed objects.

`PYTHONMALLOC=malloc` is a different diagnostic: it replaces CPython's object/memory allocator with the platform C `malloc()` allocator. That can be useful later for testing whether allocator behavior itself contributes materially to a confirmed hotspot, but it does not attribute allocations to engine code and is not the first-line tool for semantic copy optimization.

## What to compare

For wall-clock comparisons, prefer the median across several repeats. The fastest sample is useful for spotting scheduler/noise effects, while the median is a more stable default comparison statistic.

Compare results only when the scenario configuration and software/environment are meaningfully equivalent. Hosted CI runner timing is useful for directional evidence and smoke measurement but should not be treated as a precise absolute performance contract.

The repository intentionally does **not** fail CI on a fixed seconds threshold at this stage. Absolute wall-clock gates on shared hosted runners are noisy and can create false regressions. Functional tests instead protect the measurement harness itself; performance regression thresholds should be introduced only after enough baseline history exists to set statistically defensible limits.

## Optimization order

Use the profile in this order:

1. Identify the functions/stages with the largest cumulative runtime contribution.
2. Look for algorithmic improvements and avoid repeated work.
3. Reduce unnecessary object creation, copying, and conversion in confirmed hot paths.
4. Improve data structures/layout when profiling shows lookup or traversal costs dominate.
5. Consider vectorization or compiled acceleration only for remaining isolated kernels whose cost justifies the added complexity.

The public simulation/kernel contracts should remain stable during optimization. A faster implementation is not a reason to reintroduce biological assumptions into the domain-neutral kernel or to bypass invariant-preserving domain APIs.
