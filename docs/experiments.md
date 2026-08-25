# Reproducible Experiments and Export

The experiment layer runs independent reference-ecology replicates without
coupling experiment orchestration back into the simulation domains.

`run_reference_replicates()` creates a fresh reference ecology for every seed.
Each replicate therefore receives a new world, simulation RNG, engine, and
observation stack.

```python
from evo_engine.experiments import run_reference_replicates
from evo_engine.presets import ReferenceEcologyConfig

config = ReferenceEcologyConfig(max_steps=100)
result = run_reference_replicates(config, seeds=(101, 102, 103, 104))
```

## Reproducibility metadata

Every `ReferenceReplicateResult` includes immutable `RunMetadata` containing:

- the replicate seed,
- installed engine package version,
- Python version,
- canonical JSON for the complete reference configuration,
- ordered trait names,
- ordered locus names, and
- the number of committed simulation steps.

The canonical configuration JSON is sorted and compact, so equivalent
configurations have a stable textual representation. The baseline
`ReferenceEcologyConfig` remains immutable; only its `seed` field is evolved for
each replicate.

## Recorded results

A replicate stores final population, carcass, and environmental-resource totals
along with the full committed population, genetic-composition, pedigree, and
event-count histories. Population history includes mating-type composition at
every recorded step in addition to age, energy, body mass, resources, and
configured phenotype traits.

Birth and biological-death totals are derived from the pedigree/lifetime records
rather than from generic world removals. This preserves the mortality semantics
established by the observation stack: future migration or non-mortality removals
do not become deaths merely because an organism leaves the active world.

## Export

The package intentionally does not require pandas for core experiment export.
Standard-library writers provide:

```python
from evo_engine.experiments import (
    write_experiment_json,
    write_population_history_csv,
    write_replicate_summary_csv,
)

write_experiment_json(result, "outputs/experiment.json")
write_replicate_summary_csv(result, "outputs/replicates.csv")
write_population_history_csv(result, "outputs/population_history.csv")
```

The JSON export retains the rich nested observation structures, including
`mating_type_counts` in each population observation.

The replicate-summary CSV contains one row per seed. In addition to the fixed
run/final-state fields, it emits:

```text
final_mating_type_count:<mating-type>
```

for every mating-type label observed anywhere in the experiment.

The population-history CSV is tidy with one row per replicate and committed
observation step. It includes age, energy, body-mass, and configured trait means
plus:

```text
mating_type_count:<mating-type>
```

columns. The mating-type columns are the deterministic sorted union of labels
observed across all replicate histories. A label absent from a particular step
receives count zero, which makes type loss, skew, extinction, or later appearance
straightforward to analyze in ordinary tabular tools.

## Architecture boundary

`evo_engine.experiments` is a top-level consumer. It may compose presets and
observation results, but production simulation packages must not import the
experiment runner. Import Linter enforces this direction so reusable biological
and engine domains remain independent of research-workflow orchestration.
