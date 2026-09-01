# Performance Measurement

Performance work follows a measurement-first rule: establish a reproducible workload, profile it, and optimize the measured hotspot before considering lower-level acceleration.

Readability and semantic correctness are hard constraints. An optimization is not worthwhile merely because it is measurable: it must also preserve clear control flow, explicit invariants, and maintainable abstractions.

## Kernel-only baselines

Kernel optimization uses synthetic, domain-neutral scenarios rather than the reference ecology. This prevents modeled-domain work from being mistaken for orchestration overhead.

The fixed kernel scenarios each run `50` steps with `100` generic events per step:

- **`kernel-core`** exercises proposal, resolution, materialization/application orchestration, transactional state copying, and committed telemetry without a mutation journal.
- **`kernel-journaled`** runs the same workload with a generic optional mutation journal so checkpoint/effect-capture overhead remains visible.

The synthetic workload does not import biological, ecological, world, or concrete process packages. Reference-ecology profiles remain useful for end-to-end performance work, but they must not be used to identify kernel-only optimization targets because their stage times include modeled-domain execution.

Run the kernel profiler from the repository root:

```bash
venv/bin/python scripts/profile_kernel.py
```

Useful focused runs include:

```bash
venv/bin/python scripts/profile_kernel.py --scenario core
venv/bin/python scripts/profile_kernel.py --scenario journaled
venv/bin/python scripts/profile_kernel.py --scenario all --repeats 5 --warmups 2 --top 40
```

Kernel artifacts use the same benchmark JSON, human-readable profile, and raw `pstats` formats described below for the reference scenarios.

### Post-#72 structural baseline

After the kernel optimization series through PR #72, the fixed `5,000`-event synthetic profiles produced these deterministic call counts:

- `kernel-core`: **47,604 function calls**
- `kernel-journaled`: **67,804 function calls**

These counts are more useful than cross-run hosted wall-clock comparisons because GitHub-hosted runner speed varies. The journaled scenario intentionally retains a fresh `mutation_count` read before every applied event and therefore measures the cost of the dynamic optional-journal contract rather than assuming journal capability is static.

At this point the largest remaining generic per-event cost is committed `AppliedEvent` creation. The kernel has already removed redundant validation from its trusted internal construction path while retaining public validation and process-carried event-index validation. The remaining cost is predominantly the actual allocation and immutable field assignment needed to preserve committed causal telemetry.

`SimulationState.copy()` still uses the ordinary validated `SimulationState` constructor after cloning the world and RNG. In the post-#72 kernel-core profile, that constructor-validation path contributed only about `0.42 ms` across all `50` transactional copies. Introducing a second mutable-state construction path for that small saving would increase maintenance cost and obscure the state invariant boundary, so it is intentionally not optimized.

### Optimization boundary

Do not force further kernel micro-optimizations when the speedup depends on making the implementation harder to read or weakening semantics. In particular, the current design intentionally rejects the following shortcuts:

- **Do not cache absence of a mutation journal across a stage.** A domain state may expose journal capability dynamically; each event must continue to obtain the current checkpoint before application.
- **Do not bypass process-carried event-step validation.** `AppliedEvent.event_step_index` originates on the materialized event rather than from kernel-owned metadata.
- **Do not add a separate no-materializer stage algorithm merely to avoid small dispatch costs.** Stage simultaneity and one linear coordination flow are more valuable than a special-case fast path.
- **Do not replace committed `AppliedEvent` objects with a less expressive representation solely to reduce allocation cost.** A representation redesign requires an independent architectural reason and full API/telemetry analysis.
- **Do not add a second trusted `SimulationState` constructor solely to skip the small copy-validation cost.** The current public construction path is clearer and the remaining measured cost is minor.
- **Do not use local-variable binding, duplicated loops, or similar interpreter-level tricks unless profiling shows a material improvement and the resulting code is at least as readable.**

Future kernel optimization should resume only when a profile reveals a new structural source of repeated work, an algorithmic improvement, or a representation change that is independently justified by the architecture. Otherwise, performance work should move outward to whichever non-kernel layer is actually dominant in the end-to-end workload.

## Reference baselines

The engine defines two fixed performance scenarios using the default `ReferenceEcologyConfig` (`20` founders, `50` steps, seed `42`):

- **`reference-core`** builds the reference simulation and lifecycle without observers. It measures simulation execution and domain/process costs without observation overhead.
- **`reference-observed`** runs the same ecology through the complete reference observation and telemetry stack. Comparing it with the core scenario exposes the additional cost of observability.

Both scenarios time only `SimulationEngine.run(...)`. Configuration, object construction, and profiler/report serialization are deliberately outside the measured wall-clock interval.

Every warmup and measured repeat is built from fresh deterministic state. Repeated measured runs must finish with the same high-level outcome dimensions (completed steps, population size, carcass count, and total resources), otherwise the benchmark fails rather than comparing unlike executions.

## Run the reference profiler

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

The GitHub Actions quality workflow runs both fixed kernel scenarios and both fixed reference scenarios as informational performance checks and uploads the same `outputs/performance/` files as a retained workflow artifact. This preserves the exact JSON, text profile, and raw `pstats` inputs used for later comparisons instead of relying only on console logs.

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

For kernel optimization across different hosted runners, prefer structural evidence such as exact function-call deltas and targeted self/cumulative profile paths. Use absolute timing only when the before/after measurements were gathered in meaningfully comparable environments.

## Optimization order

Use the profile in this order:

1. Identify the functions/stages with the largest cumulative runtime contribution.
2. Look for algorithmic improvements and avoid repeated work.
3. Reduce unnecessary object creation, copying, and conversion in confirmed hot paths.
4. Improve data structures/layout when profiling shows lookup or traversal costs dominate.
5. Consider vectorization or compiled acceleration only for remaining isolated kernels whose cost justifies the added complexity.

At every step, reject a candidate if the implementation becomes harder to understand without a correspondingly important architectural or performance benefit. The public simulation/kernel contracts should remain stable during optimization. A faster implementation is not a reason to reintroduce biological assumptions into the domain-neutral kernel, bypass invariant-preserving APIs, or make dynamic contracts artificially static.
