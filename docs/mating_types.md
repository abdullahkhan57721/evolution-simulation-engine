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

`DifferentMatingTypes` is the first built-in mating-type compatibility policy. It
accepts a pair whenever the parents carry different labels. The rule is agnostic
to the number and names of types, so two-type and multi-type systems use the same
implementation.

Mating-type compatibility composes with the existing mating rules through
`AllOfMatingCompatibility`. A pair can therefore be required to satisfy all of:

- mating-type compatibility,
- mutual mate-search range,
- mutual signal acceptance, and
- any future compatibility policy.

The same composed compatibility object can be used by mate-seeking movement and
by final parent selection, preventing organisms from deliberately moving toward
partners they could never reproduce with.

## Offspring assignment

Offspring mating type is assigned by an `OffspringMatingTypeModel` during
`Reproduction.materialize_event()`.

Built-in assignment policies include:

- `FixedMatingType`, which assigns one deterministic label; and
- `RandomMatingType`, which chooses uniformly from an arbitrary tuple of labels.

Assignment occurs only after a reproduction proposal has survived conflict
resolution. Candidate pair generation does not sample offspring mating type.
Rejected mating proposals therefore consume no assignment RNG and cannot alter
the stochastic trajectory of births that actually occur.

The chosen mating type is stored in the materialized `Reproduction.Event`.
`apply_event()` is then mechanical: it charges the already-recorded parental
energy contributions and inserts an offspring with the already-determined mating
type, genome, genetic phenotype, developmental profile, body mass, and location.

## Mating-type-specific parental investment

Reproductive identity may also alter energetic cost without making parent tuple
order a biological role.

`MatingTypeScaledInvestment` wraps any existing `ParentalInvestment` policy. The
wrapped policy first computes one base investment for each parent, after which a
`MatingTypeInvestmentScale` multiplies each amount according to that organism's
immutable mating type.

```text
base parental investment
        ↓
identify each parent's mating type
        ↓
apply mating-type rational scale
        ↓
validated integer energy contribution
```

The scale is represented by an integer numerator and positive denominator and
uses deterministic half-up rounding. Unconfigured mating types receive an
implicit neutral `1/1` scale rather than being silently assigned one of the
configured asymmetric roles.

Because this is a wrapper, mating-type asymmetry composes with heritable
investment. For example, a parent may express `offspring_energy=5`, while its
mating type determines whether that value is scaled upward, downward, or left
unchanged. The wrapper also forwards the wrapped policy's genetic trait
requirements into engine preflight.

## Reference ecology

The reference ecology uses two neutral labels:

```text
type_a
type_b
```

Founders alternate deterministically between the two labels. Even founder
populations are exactly balanced; odd populations differ by one individual.
Founder assignment consumes no simulation RNG.

Reference mating requires different mating types in addition to the existing
search-range and mutual-signal requirements. Resolved offspring receive
`type_a` or `type_b` with equal probability using the simulation RNG.

The reference ecology now also demonstrates asymmetric reproductive energetic
burden. Its default heritable founder value remains:

```text
offspring_energy = 4
```

and the default mating-type scales are:

```text
type_a: 3/2  → 6 energy
type_b: 1/2  → 2 energy
```

A default `type_a`/`type_b` pair therefore still invests eight total energy units,
matching the historical `4 + 4` reference newborn-energy budget, while one mating
type bears a larger immediate reproductive cost. The scale configuration is
explicit and can be changed or made symmetric.

These labels remain deliberately neutral. The example demonstrates anisogamy-like
energetic asymmetry without claiming that `type_a` is biologically female or that
`type_b` is biologically male. Sex-specific physiology, sex chromosomes,
role-specific behavior, and other mechanisms remain separate models.

## Population observation

`PopulationObservation` records complete mating-type counts for every committed
population state. Multi-seed experiment exports preserve those counts in JSON and
emit deterministic mating-type columns in both time-series and replicate-summary
CSV outputs.

This makes reproductive identity an observable evolutionary state rather than a
hidden compatibility detail.

## Future extensions

The current boundary supports richer systems without changing the core event
pipeline. Examples include:

- compatibility matrices in which only particular mating-type pairs are valid,
- genetically determined sex or mating type,
- environmental sex determination,
- temperature- or condition-dependent assignment,
- more than two mating types,
- mating-type-specific physiology beyond reproductive investment,
- asymmetric courtship or parent roles,
- sex chromosomes or other specialized inheritance models, and
- mating systems permitting multiple successful reproductive events per parent
  within one stage.

Those mechanisms should be modeled explicitly in their appropriate domain layer
rather than by making `Organism.mating_type` itself responsible for genetics or
behavior.
