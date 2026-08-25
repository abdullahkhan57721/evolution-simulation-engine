# Mating Types and Reproductive Identity

The engine represents reproductive mating type as immutable individual state on
`Organism`, separate from genome, genetic phenotype, and developmental profile.
A mating type is an arbitrary nonempty string label such as `type_a`, `type_b`,
`male`, `female`, or a domain-specific compatibility class.

This separation is intentional. A simulation may determine sex or mating type
genetically, environmentally, stochastically, or through a more complex
developmental system. The core organism representation does not assume that
reproductive identity is always a single Mendelian trait.

## Compatibility

`DifferentMatingTypes` accepts a pair whenever the parents carry different
labels. The rule is agnostic to the number and names of types, so two-type and
multi-type systems use the same implementation.

Mating-type compatibility composes with the existing mating rules through
`AllOfMatingCompatibility`. The same composed compatibility object can be used by
mate-seeking movement and by final parent selection, preventing organisms from
deliberately moving toward partners they could never reproduce with.

## Offspring assignment

Offspring mating type is assigned by an `OffspringMatingTypeModel` during
`Reproduction.materialize_event()` after inheritance, phenotype expression, and
developmental realization.

The assignment model receives:

```text
resolved parents
inherited offspring Genome
offspring GeneticPhenotype
offspring DevelopmentalProfile
current SimulationState
simulation RNG
```

This makes reproductive identity a genuine policy boundary. Assignment can depend
on inherited state, realized developmental state, the environment, randomness, or
combinations of those inputs without putting sex-determination rules inside the
reproduction process.

Built-in assignment policies include:

- `FixedMatingType`, which assigns one deterministic label;
- `RandomMatingType`, which chooses uniformly from arbitrary configured labels;
- `GeneticPhenotypeMatingType`, which uses a categorical offspring genetic trait
  directly as the mating-type label; and
- `DevelopmentalProfileMatingType`, which uses the realized value of a
  developmental trait and therefore allows development to change reproductive
  identity relative to genetic expectation.

The two trait-based policies expose their trait dependency through
`required_traits`, so the normal engine preflight can reject a missing
sex/mating-type trait before the simulation begins.

Assignment occurs only after a reproduction proposal has survived conflict
resolution. Rejected mating proposals therefore consume no inheritance,
development, or mating-type RNG and cannot alter the stochastic trajectory of
births that actually occur.

The chosen mating type is stored in the materialized `Reproduction.Event`.
`apply_event()` is then mechanical: it charges the already-recorded parental
energy contributions and inserts an offspring with the already-determined mating
type, genome, genetic phenotype, developmental profile, body mass, and location.

## Genetic and environmental determination

`GeneticPhenotypeMatingType` deliberately does not prescribe a chromosome system.
The configured genetic architecture decides how one or more loci become the
categorical trait value. The assignment model simply consumes that expressed
value. This allows simple Mendelian systems now and richer sex-chromosome or
polygenic models later without changing `Reproduction`.

`DevelopmentalProfileMatingType` reads the corresponding realized developmental
value instead. Because the development API already accepts `SimulationState`, an
environment-aware `DevelopmentModel` can eventually implement temperature-,
condition-, or genotype-by-environment-dependent determination before this policy
assigns the immutable organism mating type.

This preserves the project boundary:

```text
Genome
    → GeneticArchitecture
        → GeneticPhenotype
            → DevelopmentModel + environment
                → DevelopmentalProfile
                    → OffspringMatingTypeModel
                        → immutable Organism.mating_type
```

## Mating-type-specific parental investment

Reproductive identity may also alter energetic cost without making parent tuple
order a biological role.

`MatingTypeScaledInvestment` wraps any existing `ParentalInvestment` policy. The
wrapped policy first computes one base investment for each parent, after which a
`MatingTypeInvestmentScale` multiplies each amount according to that organism's
immutable mating type. Rational scales use deterministic half-up rounding, and an
unconfigured mating type receives a neutral `1/1` scale.

Because this is a wrapper, mating-type asymmetry composes with heritable
investment. A parent may express `offspring_energy=5`, while its mating type
determines whether that value is scaled upward, downward, or left unchanged. The
wrapper forwards the nested policy's genetic trait requirements into engine
preflight.

## Reference ecology

The reference ecology currently uses two neutral labels:

```text
type_a
type_b
```

Founders alternate deterministically between the two labels. Reference mating
requires different mating types in addition to the existing search-range and
mutual-signal requirements. Resolved offspring currently receive `type_a` or
`type_b` with equal probability using the simulation RNG; the reference preset
has not yet selected a particular genetic or environmental sex-determination
model.

The reference ecology also demonstrates asymmetric reproductive energetic burden.
Its default heritable `offspring_energy=4` is scaled as:

```text
type_a: 3/2  → 6 energy
type_b: 1/2  → 2 energy
```

A default pair therefore still invests eight total energy units, matching the
historical `4 + 4` reference newborn-energy budget, while one mating type bears a
larger immediate reproductive cost. These values are integration defaults, not a
calibrated biological estimate.

The labels remain deliberately neutral. The example demonstrates
anisogamy-like energetic asymmetry without claiming that `type_a` is biologically
female or that `type_b` is biologically male.

## Population observation

`PopulationObservation` records complete mating-type counts for every committed
population state. Multi-seed experiment exports preserve those counts in JSON and
emit deterministic mating-type columns in both time-series and replicate-summary
CSV outputs.

## Future extensions

The current boundary supports richer systems without changing the core event
pipeline. Important extensions include:

- compatibility matrices in which only particular mating-type pairs are valid;
- an explicit reference genetic or environmental determination system;
- sex chromosomes or other specialized inheritance models;
- mating-type-specific physiology beyond parental investment;
- asymmetric courtship or parent/gamete roles;
- more than two mating types; and
- mating systems permitting multiple successful reproductive events per parent
  within one stage.

Those mechanisms should be modeled explicitly in their appropriate domain layer
rather than by making `Organism.mating_type` itself responsible for genetics,
development, or behavior.
