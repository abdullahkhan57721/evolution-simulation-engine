# Controlled Clonal Locomotion System

E2 introduces a deliberately minimal experimental composition for asking what an
inherited locomotor-capacity trait mechanically does before asking whether natural
selection changes that trait.

It is separate from the richer reference ecology and B3 flagship.

## Scientific boundary

The controlled system is:

```text
one inherited max_speed locus
        +
clonal one-parent reproduction
        +
fixed nonfocal biology
        +
perfect full-world resource sensing
        +
deterministic nearest-resource targeting
        +
explicit locomotion-use cost
        +
no mutation
```

The frozen simulation kernel, general ploidy, sexual inheritance, recombination,
and mating-system architecture are unchanged. E2 composes existing policies above
those layers.

## What `max_speed` means

Keep four ideas separate:

```text
inherited max_speed
        ↓
operative movement capacity
        ↓
target-directed movement decision
        ↓
actual committed displacement
```

E2 deliberately has no development stage. `GeneticPhenotypeCharacteristics` reads
operative `max_speed` directly from raw genetic expression, so inherited and
operative values are numerically equal in this composition while remaining
scientifically distinct concepts. Actual movement can be shorter than capacity
because the target is close or because an integer grid cannot represent the
continuous capacity boundary exactly at a given bearing.

The E1 measurement layer remains authoritative for actual displacement. It derives
realized distance from committed `OrganismMoved` evidence rather than renaming an
attempted displacement or inherited capacity as speed.

## Isolated energetic baseline

The controlled composition omits the reference ecology's separate `max_speed`
maintenance burden. The only movement-specific energetic burden is the configured
power-law locomotion-use cost:

```text
cost = coefficient × body_mass^mass_exponent × distance^distance_exponent
```

E2 fixes the mass exponent to zero, fixes body mass across organisms, and defaults
the distance exponent to two. With the default unit coefficient this reduces to
squared attempted Euclidean grid displacement. The applied movement event records
the authoritative charged cost, and E1 derives the scientific measurement from
that event.

This is a mechanics baseline, not a claim that biological travel universally has a
quadratic energy law.

## Movement and perception

Every organism is assigned the energy-acquisition movement purpose. Resource
perception is perfect and the fixed sensory radius spans the complete rectangular
world. `NearestResourceTarget` therefore chooses the nearest extant resource
deterministically; no detection RNG is involved.

If no resource remains, the controlled composition uses a stationary fallback.
It does not switch to blind random exploration, so a large `max_speed` cannot gain
an accidental multi-cell exploration/tunneling advantage.

Targeted movement uses `StraightLineTowardTarget`. Targets inside capacity are
reached exactly without overshoot. Distant targets are projected toward the
capacity boundary and then represented by an integer grid displacement.

## Grid anisotropy

A Euclidean speed disk does not map perfectly onto integer coordinates. For the
same `max_speed`, some bearings can realize the full capacity while others realize
a slightly shorter displacement after projection and rounding.

`run_locomotion_bearing_assay` exposes this directly. E2 treats the difference as
a diagnostic property of the discrete model rather than smoothing it away or
pretending that a continuous travel equation is an exact oracle.

The canonical mechanics assay pads the founder and resource target away from every
world edge. Because target-directed movement follows the segment between two
in-bounds points and never overshoots the target, boundary clamping should not
change the attempted displacement in that assay. Tests require attempted and
committed distances to agree.

The mechanics assay also supplies nonlimiting one-step energy across the complete
E2 `max_speed` domain, so starvation cannot censor the measurement being validated.
That assay-only choice does not change the reusable controlled composition's
ordinary energy accounting.

## Feeding and competition

Resource consumption occurs at the organism's committed endpoint after the
movement stage. There is no path-integrated feeding: crossing a coordinate does
not itself consume resources.

The world permits organisms to occupy the same coordinate, so converging movement
requests do not create a collision winner or a hidden organism-ID priority. When
multiple co-located organisms then request the same limited resource, the
controlled composition uses the existing random-order allocation resolver. This
avoids a permanent proposal-order/low-ID winner for indivisible scarce resources,
while making the winner seed-dependent. The canonical single-organism mechanics
assay contains no resource competition; multi-organism allocation is diagnostic
evidence and later experiments must preserve the run/seed as the replicate.

## Clonal propagation

The reproduction stage reuses existing `SingleParent` and `ClonalInheritance`
policies. `NoMutation` is attached to the sole `max_speed` locus. Nonfocal energy
investment and newborn body mass are fixed simulation-wide values.

Movement never has a reproduction purpose, so reproductive success cannot acquire
a hidden mate-finding speed benefit in this controlled system.

## Theory and claim boundary

A continuous travel-cost calculation can motivate hypotheses, but it is not an
exact prediction for the simulation. Integer rounding, discrete timesteps,
resource depletion, local consumption, competition, and demographic events can
all break a continuous closed-form optimum.

E2 validates mechanics only. It does **not** claim evolutionary adaptation or an
optimal evolved `max_speed`. E3 may use monomorphic populations to measure an
independent ecological performance landscape; only later may E4 ask whether
standing inherited variation changes in the predicted direction.
