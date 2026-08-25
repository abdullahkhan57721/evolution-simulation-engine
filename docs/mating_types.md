# Mating Types and Reproductive Identity

The engine represents reproductive mating type as immutable individual state on
`Organism`, separate from genome, genetic phenotype, and developmental profile.
A mating type is an arbitrary nonempty string label such as `type_a`, `type_b`,
`male`, `female`, or a domain-specific compatibility class.

This separation is intentional. A simulation may eventually determine sex or
mating type genetically, environmentally, stochastically, or through a more
complex developmental system. The core organism representation does not assume
that reproductive identity is always a single Mendelian trait.

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

## Reference ecology

The reference ecology uses two labels:

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

These labels are deliberately neutral. They demonstrate a two-type reproductive
system without embedding assumptions about anisogamy, sex-specific parental
investment, sex chromosomes, sexual dimorphism, or parent roles. Those can be
added later as explicit models rather than being implied by the words “male” and
“female.”

## Future extensions

The current boundary supports richer systems without changing the core event
pipeline. Examples include:

- compatibility matrices in which only particular mating-type pairs are valid,
- genetically determined sex or mating type,
- environmental sex determination,
- temperature- or condition-dependent assignment,
- more than two mating types,
- sex-specific or mating-type-specific physiology and energetic costs,
- asymmetric parent roles and parental investment, and
- sex chromosomes or other specialized inheritance models.

Those mechanisms should be modeled explicitly in their appropriate domain layer
rather than by making `Organism.mating_type` itself responsible for genetics or
behavior.
