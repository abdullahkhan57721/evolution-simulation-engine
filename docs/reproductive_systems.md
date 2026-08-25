# Reproductive Roles and Mating Systems

The reproduction layer distinguishes three concepts that should not be collapsed
into one field:

- **mating type** is immutable reproductive identity stored on an organism;
- **reproductive role** is a contextual capability in a particular mating
  system; and
- **parent tuple order** is meaningful only for selectors that explicitly define
  ordered roles.

This separation supports binary, multi-type, hermaphroditic, and asymmetric
systems without hard-coding male/female semantics into the engine.

## Compatibility networks

`MatingTypeCompatibilityMatrix` represents an explicit unordered network of
compatible mating-type pairs. It complements `DifferentMatingTypes`.

For example, a three-type system can permit A×B and B×C while rejecting A×C,
or it can explicitly permit same-type combinations such as B×B. Reversed pair
entries are canonicalized, so A×B and B×A are the same compatibility rule.

## Contextual reproductive roles

`ReproductiveRoleModel` determines which role labels an organism may occupy in a
mating system.

`MatingTypeRoles` maps mating-type labels to zero, one, or multiple role labels.
An organism with mating type `hermaphrodite` may therefore expose both `chooser`
and `signaler` roles without acquiring multiple mating-type identities.

Roles are not stored on `Organism`; they are derived by a policy. Future role
models can therefore depend on age, condition, developmental phenotype, social
state, or other context without changing organism identity.

## Directed parent selection

Existing `PairwiseMating` uses unordered combinations and treats the two parent
positions as interchangeable.

`DirectedPairwiseMating` is explicitly different. It requires a `first_role` and
`second_role`. Every emitted `ParentGroup` is ordered so:

```text
parent_ids[0] -> first_role
parent_ids[1] -> second_role
```

The selector uses an ordered Cartesian pairing of role-qualified candidates,
skips self-pairing, applies the configured spatial neighborhood, and then applies
directed compatibility and preference policies.

That order guarantee is local to this selector. Generic reproduction code does
not reinterpret parent index zero as a universal biological sex or role.

## Directed mate choice

`ChooserSignalCompatibility` reads a threshold trait from the first parent and a
signal trait from the second parent. The signaler is acceptable when its signal
meets the chooser's threshold.

`ChooserSignalMarginPreference` scores the same ordered pair by:

```text
signaler signal - chooser threshold
```

These policies provide asymmetric mate choice without changing the symmetric
`MatingCompatibility` and `MatingPreference` protocols or the existing mutual
signal policies.

## Multiple successful matings

`CapacityPreferenceOrder` resolves `Reproduction.Proposal` objects in descending
preference order while limiting how many accepted proposals may involve each
parent during the stage.

```text
max_events_per_parent = 1  -> exclusive-parent mating
max_events_per_parent = 2  -> up to two accepted matings per parent
...
```

Every participant in a proposal must still have remaining capacity. This models
a mating-system constraint at resolution time rather than changing inheritance
or reproduction materialization.

## Composition

The policies can be combined independently:

```text
mating type
    -> contextual role model
    -> directed parent selection
    -> compatibility matrix / signal acceptance
    -> directed preference score
    -> capacity-aware conflict resolution
    -> normal Reproduction materialization
```

Mating-type-specific parental investment remains a separate layer. A role-aware
mating system can therefore coexist with asymmetric energetic investment without
requiring either concept to define the other.

## Deliberate boundaries

The engine still does not assume specialized sex chromosomes, fixed female/male
roles, pair bonds, pregnancy, parental care, or permanent social relationships.
Those mechanisms can be added as explicit policies or state models where they
belong instead of being inferred from tuple order or mating-type names.
