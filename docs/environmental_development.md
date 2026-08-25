# Environmental Development and G×E

The development layer can now make an organism's realized developmental targets
depend on environmental exposure without changing its inherited genome or
`GeneticPhenotype`.

This preserves the existing causal boundary:

```text
Genome
  ↓ deterministic genetic expression
GeneticPhenotype
  ↓ developmental model + environmental exposure
DevelopmentalProfile
  ↓ physiology, behavior, life history, reproductive identity
realized organism state
```

## Developmental location

`DevelopmentLocation(x, y)` represents the coordinate at which developmental
exposure is evaluated. It is a small development-domain value object rather than
a field on `SimulationState`.

`Organism.from_genome()` passes its initial coordinate as its developmental
location. Development models may ignore location, use it to sample a spatial
field, or use an aggregate exposure policy instead.

The generic `DevelopmentModel` and `TraitDevelopmentModel` contracts accept both
an optional `SimulationState` and optional `DevelopmentLocation`. Deterministic
and stochastic nonenvironmental development ignore those values.

## Environmental sampling

Environmental effects explicitly separate **what response occurs** from **how the
environment is sampled**.

`LocalEnvironmentalSampling` reads the named field at `DevelopmentLocation` and
fails if no location exists.

`WorldMeanEnvironmentalSampling` computes the arithmetic mean across the world
grid. It is suitable for genuinely global developmental exposures and for
pipelines in which a specific developmental coordinate is intentionally not
part of the model.

No environment-aware model silently substitutes an arbitrary coordinate.

## Additive plasticity

`LinearEnvironmentalDevelopment` implements:

```text
P = G + slope × (E - E_ref)
```

`G` is the genetically expressed target, `E` is sampled environmental exposure,
and `E_ref` is the reference environment. All genotypes receive the same
environmental slope, so this represents phenotypic plasticity but not a
 genotype-dependent environmental sensitivity.

## Genotype-by-environment interaction

`GenotypeScaledEnvironmentalDevelopment` implements:

```text
P = G × (1 + sensitivity × (E - E_ref))
```

The reaction-norm slope is proportional to `G`. Different genetic values
therefore respond by different absolute amounts to the same environmental
change. This is an explicit genotype-by-environment interaction rather than a
simple additive environmental offset.

Both integer models use deterministic half-away-from-zero rounding and support
optional inclusive minimum/maximum developmental bounds.

## Environmental categorical determination

`EnvironmentalThresholdDevelopment` maps environmental exposure to one of two
configured developmental values. The inherited value remains in
`GeneticPhenotype`, while the environmental result is stored in the
`DevelopmentalProfile`.

This can model environmental reproductive-identity determination without making
`Organism.mating_type` responsible for development. Combined with
`DevelopmentalProfileMatingType`, the causal path is:

```text
inherited reproductive-identity trait
            ↓
environmental threshold development
            ↓
DevelopmentalProfile reproductive identity
            ↓
DevelopmentalProfileMatingType
            ↓
immutable offspring mating_type
```

The engine therefore supports genetic, stochastic, and environmental mating-type
determination through separate policies.

## Environmental dynamics

Time-varying environmental fields are modeled by forcing policies in
`evo_engine.ecology` and the `EnvironmentalChange` simulation process.

Built-in forcing models are:

- `LinearEnvironmentalForcing` for directional change;
- `SinusoidalEnvironmentalForcing` for periodic/seasonal change; and
- `ScheduledEnvironmentalForcing` for discrete disturbances, pulses, or regime
  changes.

A forcing model only calculates a target value. `EnvironmentalChange` applies
that value to either the complete grid or an explicit coordinate patch through
`WorldState.set_environmental_value()`. Effective changes therefore enter the
same transaction-local telemetry journal as other world mutations.

This separation keeps environmental state, temporal forcing, and biological
response independently replaceable.

## Deliberate boundary

Developmental profiles remain lifetime-immutable. These models represent
conditions acting during developmental realization. Reversible adult plasticity
should be modeled as mutable physiology/process state rather than by rewriting a
`DevelopmentalProfile` after birth.
