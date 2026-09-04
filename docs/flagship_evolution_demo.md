# Confirmed flagship evolutionary demonstration

The current scientific flagship is a **matched environment-dependent selection
experiment** built entirely from the ordinary reference ecology. It asks whether
changing renewable-resource geography changes the evolutionary fate of standing
heritable `max_speed` variation.

This is an illustrative engine/reference-ecology result. It is not a calibrated
prediction about a real species or ecosystem.

## Question

> Does compact spatial resource geography change selection on existing heritable
> `max_speed` standing variation relative to a matched uniform-resource
> environment in the current richer reference ecology?

The scenario deliberately keeps the ordinary sexual reference ecology rather than
reducing the system to an isolated movement toy model.

## Frozen matched design

Both arms use the same:

- `12 × 12` world;
- 20 deterministic founders;
- founder energy `30`;
- 50 committed timesteps;
- 32 renewable deposits per timestep;
- 6 resource units per deposit;
- balanced homozygous `max_speed = 1` and `max_speed = 4` founders;
- initial high-speed allele frequency `0.50`;
- shared `max_intake_rate = 8`;
- mutation probability `0`;
- reference mating types and sexual inheritance;
- mating radius `3`;
- frozen reference movement, sensing, physiology, feeding, reproduction,
  recombination, starvation, and age-mortality mechanisms;
- founder `attack_strength = 0` and `defense = 1`, retaining the ordinary
  predation stage while preventing the focal scenario from gaining a predation
  advantage through the attack/defense background.

The treatment-integrity audit requires the canonical same-seed arms to be equal
after replacing only the treatment resource-placement policy with the control
policy.

### Control

Renewable resources use `UniformResourcePlacement()`.

### Compact treatment

Renewable resources use two equal-weight radius-1 circular patches centered at:

```text
(2, 5)
(9, 5)
```

### Falsification/sensitivity condition

The predeclared geometry sensitivity keeps the same centers, renewable-resource
quantity, and all biology but broadens the patch radius from `1` to `2`.

## Focal inherited variation

`max_speed` means **genetic-phenotype maximum movement capacity**, not realized
movement speed on every step.

The balanced founder construction starts with:

- 10 homozygous speed-1 founders;
- 10 homozygous speed-4 founders;
- equal representation of both speed variants within each reference mating type.

The high-speed allele therefore starts at frequency `0.50` in every run.

The inherited performance axis already existed before B3. Higher `max_speed` can
permit farther realized movement toward the same target, while the ordinary
reference physiological-maintenance model gives the speed-4 background a higher
ongoing energetic cost than speed 1. B3 adds no generic fitness or strategy
abstraction; selection emerges through ordinary ecological interaction, survival,
and sexual reproduction.

## Discovery versus confirmation

The candidate was selected during an exploratory B3 search using discovery seeds:

```text
11, 23, 37, 41, 59, 73, 89, 101
```

Those seeds were repeatedly exposed while comparing resource densities and
geometries and therefore do **not** count as independent confirmation.

Before any confirmation result was inspected, B3 froze a disjoint confirmation
set:

```text
5, 17, 29, 43, 61, 79, 97, 113
```

The replicate is one simulation run. Control and treatment are blocked by seed,
but treatment can change later RNG consumption through changed ecological state;
this is not claimed to be perfect common-random-number coupling.

## Primary evolutionary result

The predeclared headline readout is high-speed allele frequency at committed step
30. Compact minus matched uniform control is the paired effect.

| Seed | Uniform | Compact radius 1 | Compact - uniform | Radius 2 |
| ---: | ---: | ---: | ---: | ---: |
| 5 | 0.4250 | 0.6571 | +0.2321 | 0.5196 |
| 17 | 0.2167 | 0.5909 | +0.3742 | 0.5521 |
| 29 | 0.3704 | 0.5200 | +0.1496 | 0.4405 |
| 43 | 0.5217 | 0.5606 | +0.0389 | 0.4091 |
| 61 | 0.3857 | 0.5500 | +0.1643 | 0.6136 |
| 79 | 0.2647 | 0.7436 | +0.4789 | 0.4390 |
| 97 | 0.2667 | 0.5909 | +0.3242 | 0.4022 |
| 113 | 0.2875 | 0.8000 | +0.5125 | 0.6630 |

Across all eight independent confirmation seeds:

- mean uniform step-30 high-speed allele frequency = **0.3423**;
- mean compact radius-1 step-30 high-speed allele frequency = **0.6266**;
- mean paired compact-minus-uniform effect = **+0.2843**;
- compact treatment exceeded its matched uniform control in **8/8** seeds;
- mean uniform fell below the founder baseline `0.50` while mean compact rose
  above it;
- all canonical uniform and compact runs remained non-extinct through the full
  50-step horizon.

Full allele/genotype and focal-trait trajectories remain part of the run evidence;
step 30 is the frozen headline comparison rather than the only retained timestep.

## Differential reproductive contribution

Founder realized reproductive success over the full 50-step horizon is the
primary demographic mechanism readout.

Uniform environments favored the low-speed founder mean over the high-speed mean
in **6/8** confirmation seeds; the other two were ties. Compact radius-1 patches
favored high-speed founders in **7/8** seeds.

This supports the causal bridge:

```text
resource geography
        ↓
individual ecological opportunity under inherited movement capacity/cost
        ↓
repeated survival and reproductive interactions
        ↓
differential realized reproductive contribution
        ↓
change in allele/genotype composition
```

The result is not interpreted as a direct isolated estimate of locomotion cost,
feeding benefit, or mate-search benefit. Those mechanisms interact inside the
reference ecology.

## Resource-manipulation evidence

Renewable-resource quantity is matched exactly across canonical arms:

```text
32 deposits/step × 50 steps = 1,600 renewable-generation events
1,600 × 6 units = 9,600 generated resource units
```

Committed `ResourceGeneration` events provide provenance-safe evidence about the
renewable manipulation:

- every compact-treatment renewable-generation event lies inside the frozen
  radius-1 patch support;
- uniform renewable generation is not confined to that support;
- generated deposit count and total generated amount are equal between matched
  arms.

`SpatialObservation.resources` has a different meaning: it is the complete
committed world resource state and can also include resource returned through
carcass decomposition. It is therefore used to describe realized resource
geography, not to assert provenance of every resource unit.

## Geometry sensitivity

The radius-2 sensitivity weakens the compact-treatment advantage in aggregate:

- radius-1 compact mean at step 30: **0.6266**;
- radius-2 mean at step 30: **0.5049**.

Per-seed radius-2 behavior is intentionally reported rather than hidden; radius 2
does not weaken the high-speed frequency for every individual seed. The supported
claim is aggregate and specific to this tested geometry. B3 does **not** claim that
"patchiness" generically favors high speed.

## Founder-label counterbalance

A bounded confounding check was predeclared for confirmation seeds `29` and `79`.
For those runs, the speed values assigned to the deterministic founder ID/position
pattern were swapped while IDs, coordinates, mating types, nonfocal traits, and
environmental configuration remained fixed.

The compact-minus-uniform effect remained positive in both counterbalanced checks.
This supports interpretation of the treatment effect as following `max_speed`
state rather than the original deterministic focal-label placement.

## Deterministic representative run

The representative storytelling seed was selected only after all confirmation
runs were complete using the predeclared rule:

1. compute each confirmation seed's paired step-30 effect;
2. take the median paired effect;
3. among non-extinct matched pairs with at least one authoritative
   targeted-movement/resource-consumption episode, choose the effect closest to
   the median;
4. break an exact tie with the lower seed.

The median paired effect is **0.2782** and the selected representative seed is
**5**.

This seed is a storytelling example, not robustness evidence.

## Renderer-neutral scientific storyboard

This handoff supplies scientific meaning only. Interactive and cinematic
renderers independently own color, materials, layout, camera, timing,
interpolation, transitions, and interaction.

### QUESTION

Does compact renewable-resource geography alter selection on inherited
`max_speed` capacity relative to a matched uniform environment?

### ENVIRONMENTAL DIFFERENCE

Show the same world scale and renewable-resource quantity in both arms:

```text
uniform placement
        versus
same quantity generated only within two radius-1 patches
```

Do not imply that total committed world resources are all renewable deposits;
decomposition can return resources elsewhere.

### INDIVIDUAL CONSEQUENCE

Use a fixed scientific `max_speed` capacity scale from `1` to `4`. A focal
organism's encoded value comes from committed per-organism genetic-trait evidence,
not inferred movement distance.

Representative seed 5 contains real compact-treatment episodes including:

- organism `16`, speed capacity `1`, completed step `7`: moved `(4, 5) → (3, 5)`,
  realized displacement `1`, paid movement cost `1`, then consumed `8` resource
  units;
- organism `1`, speed capacity `4`, completed step `5`: moved `(2, 0) → (2, 4)`,
  realized displacement `4`, paid movement cost `2`, then consumed `8` resource
  units.

These are separate authoritative examples. They are **not** a fabricated
head-to-head contest and should not be presented as one.

### REPEATED INTERACTIONS

Preserve the ordinary ecology: sensing, resource targeting, feeding, metabolism,
movement expenditure, mating, sexual inheritance, starvation, age mortality, and
resource renewal all continue across the 50-step horizon.

### DIFFERENTIAL REPRODUCTIVE CONTRIBUTION

Use founder realized reproductive success to show that the strategy ordering
changes with environment in aggregate: lower-speed founders do better in uniform
in most confirmation runs, while higher-speed founders do better in compact
radius-1 patches in most confirmation runs.

### POPULATION CHANGE

Show population size and focal genetic composition through committed time. Do not
convert undefined post-extinction trait values to zero; the confirmed canonical
runs remain alive through step 50.

### EVOLUTIONARY EVIDENCE

The headline comparison is the matched step-30 high-speed allele frequency, with
full allele/genotype trajectories retained. Preserve a common scientific scale and
time convention across control and treatment.

### CLAIM + LIMITS

Supported claim:

> In the current reference ecology, changing only the spatial organization of
> otherwise matched renewable-resource generation changes the evolutionary fate
> of standing heritable `max_speed` variation. Compact radius-1 patches favor the
> high-speed strategy relative to matched uniform controls, while the uniform
> environment favors the lower-speed strategy in aggregate under the tested
> configuration.

Do not claim:

- that high speed is universally beneficial or universally optimal;
- that generic patchiness always favors speed;
- empirical species calibration or prediction;
- that locomotion cost alone caused the result;
- that all reference-ecology confounds have been eliminated;
- that a representative seed is evidence of robustness;
- that display interpolation, trails, annotations, or renderer-authored emphasis
  are scientific evidence.

## Running the confirmation

The canonical specification lives in
`evo_engine.presets.reference_ecology.b3_flagship`. Focused evidence analysis lives
in `evo_engine.experiments.b3_flagship`.

Run the frozen independent confirmation with:

```bash
venv/bin/python scripts/b3_confirmation.py
```

The script executes every predeclared confirmation seed, every radius-2 sensitivity
run, and both counterbalance runs. It fails if a predeclared acceptance check is
not satisfied and writes a transparent JSON evidence artifact under `outputs/`.

## Status of the earlier max-intake demonstration

The original v0.1 `max_intake_rate` demonstration remains a useful **secondary
regression/integration example**. Its helper functions and current presentation
entry points are retained for compatibility and for the v0.1 historical story.

It is no longer the primary scientific flagship after B3 confirmation. V2/V3
presentation milestones should consume the B3 scientific handoff above rather
than infer treatment/control meaning from the older max-intake example.
