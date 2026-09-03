# Flagship evolutionary demonstration

The v0.1 flagship scenario is an **illustrative evolutionary simulation** built by composing the existing reference ecology. It demonstrates how the engine connects inherited variation, ecological interaction, demographic outcomes, and measured genetic change. It is not a calibrated prediction of a real population.

## Question

> How can standing heritable differences in resource-acquisition capacity change a population under repeated spatially distributed resource opportunities?

The scenario deliberately starts with two homozygous founder variants at the existing `max_intake_rate` locus:

- 10 founders carry `max_intake_rate = 2` on both chromosome copies;
- 10 founders carry `max_intake_rate = 8` on both chromosome copies.

The variants are balanced across the two existing reference mating types, so founder genetic state is not confounded with reproductive identity. The initial high-intake allele frequency is therefore exactly `0.50`.

## Canonical configuration

The public helper `build_flagship_max_intake_specification()` defines the portfolio run:

| Setting | Value |
| --- | ---: |
| seed | `41` |
| steps | `40` |
| world | `12 × 12` |
| founder population | `20` |
| founder energy | `30` |
| resource units per deposit | `6` |
| resource deposits per step | `32` |
| mating radius | `1` |
| mutation probability | `0` |
| founder attack strength | `0` |
| founder defense | `1` |
| low max-intake allele | `2` |
| high max-intake allele | `8` |

Mutation is disabled so the demonstration follows standing variation already present at initialization. Predation is isolated through the existing attack/defense eligibility mechanism rather than by removing predation architecture. Other ecological and life-history behavior comes from the normal reference preset.

The richer resource-deposition setting should be described as a **renewable patchy-resource regime**, not as a calibrated scarcity treatment.

## Causal narrative

```text
standing inherited intake-capacity variation
        ↓
spatial resource acquisition through the normal reference ecology
        ↓
differences in energetic opportunity and demographic outcomes
        ↓
ordinary survival and sexual reproduction
        ↓
change in population trait and allele composition
```

`max_intake_rate` is not a display label. It is an existing genetic trait used by the reference resource-consumption process through the organism-specific intake-capacity model. The flagship builder changes founder genomes, then reuses the reference simulation context, lifecycle, inheritance, observers, and telemetry.

## Measured qualitative outcome

The scenario was selected through fixed- and multi-seed experimental search rather than by assuming the desired trend.

For the canonical seed `41`, the high-intake allele starts at `0.50`, is strongly above baseline by step 30, and the population remains nonzero through step 40.

The canonical robustness seed set is:

```text
11, 23, 37, 41, 59, 73, 89, 101
```

Across the measured selection sweep, every one of those seeds increased the high-intake allele above its initial `0.50` frequency and every population remained alive through the 40-step demonstration window.

Tests intentionally assert robust qualitative properties rather than fragile exact stochastic totals. Exact population counts and allele frequencies may change if legitimate stochastic implementation details evolve while preserving the causal behavior.

## Running the demonstration

### Python

```python
from evo_engine.presets import build_flagship_max_intake_ecology

ecology = build_flagship_max_intake_ecology()
ecology.engine.run(ecology.simulation)
```

### Multi-seed experiment

```python
from evo_engine.experiments import run_flagship_max_intake_replicates

experiment = run_flagship_max_intake_replicates()
```

The result uses the existing experiment result/export contracts.

### Dashboard

Launch the normal portfolio dashboard and choose **Run flagship evolution demo** in the sidebar. The dashboard keeps simulation ownership in its existing presentation model and initially focuses the population and genetics inspectors on `max_intake_rate`.

### Cinematic replay

The existing portfolio-animation example now uses the canonical flagship run:

```bash
python examples/render_portfolio_animation.py --quality low
```

The simulation completes first. Manim receives only the committed spatial/population observations through the existing renderer-neutral timeline path.

## What the demo does not claim

The reference ecology is an integration baseline designed to exercise engine architecture. The flagship scenario therefore demonstrates **software and modeling capability**, including reproducibility, inheritance, ecology, observation, and replay. It does not establish empirical effect sizes, species-specific biology, ecological calibration, or a prediction about a real ecosystem.
