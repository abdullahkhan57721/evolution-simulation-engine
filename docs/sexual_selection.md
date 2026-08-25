# Mate Choice and Sexual Selection

The reproduction domain separates questions that are often conflated in a simple
mating model:

```text
individual reproductive eligibility
    → may this organism reproduce at all?

mate discovery
    → can these organisms detect one another as potential mates?

mating compatibility
    → do both organisms accept the pairing?

pair preference
    → among compatible pairs, which pairing is favored when proposals conflict?

parental investment
    → what energetic contribution does each resolved parent make?
```

The movement system adds another separate question:

```text
mate-seeking movement
    → should an organism move toward a viable potential mate before mating?
```

Keeping these questions separate allows life history, spatial ecology, mate
search, reproductive identity, sexual selection, behavior, and energetic cost to
evolve independently.

## Parent order is not reproductive role

`PairwiseMating` still treats the ordering of the two parents as interchangeable.
Swapping the tuple order does not itself assign an initiator, receiver, female,
male, egg producer, or sperm producer role.

Reproductive asymmetry can nevertheless be explicit. `Organism.mating_type`
stores immutable reproductive identity, compatibility can depend on that label,
and parental-investment policies can apply different energetic scales to
different mating types. The asymmetry therefore follows organism state rather
than an incidental tuple position.

Future parent-selection or courtship implementations may add genuinely
role-specific behavior without changing inheritance or reproduction-event
contracts.

## Mating types

Mating types are arbitrary nonempty string labels rather than a binary sex enum.
The built-in `DifferentMatingTypes` policy accepts parents with unlike labels and
can be composed with the other compatibility rules.

The reference ecology uses neutral `type_a` and `type_b` labels, balanced among
founders and assigned to resolved offspring with equal probability. These labels
are not aliases for biological male and female; specialized sex determination,
sexual dimorphism, and sex chromosomes remain explicit future models.

## Mate search range

`MutualMateSearchRange` reads each organism's genetic `mate_search_range` and
measures pair distance with a configurable spatial metric. The default metric is
direct-grid Chebyshev distance.

A pair is discoverable only when:

```text
pair distance <= first parent's mate_search_range
and
pair distance <= second parent's mate_search_range
```

The reference ecology treats `mate_search_range` as a detection and mate-targeting
horizon, not as the distance at which reproduction itself can occur. Organisms may
detect a compatible mate several cells away, move toward that mate, and reproduce
only after reaching the configured close-range `mating_radius`.

## Choosiness and mating signal

`MutualSignalCompatibility` gives each parent an expressed:

- `choosiness`: minimum partner signal it accepts, and
- `mating_signal`: signal strength presented to potential mates.

A candidate pair is accepted only when both directions succeed:

```text
second.mating_signal >= first.choosiness
and
first.mating_signal >= second.choosiness
```

Equality is sufficient. Increasing mating signal can therefore increase mating
opportunities, while increasing choosiness can reject more potential mates.

## Pair preference

Compatibility answers whether a pair is possible. Preference answers which
compatible pair should win when an organism has multiple candidates.

`MutualSignalMarginPreference` scores the total surplus above both acceptance
thresholds:

```text
(second signal - first choosiness)
+
(first signal - second choosiness)
```

The score is symmetric. A pair exactly meeting both thresholds receives zero.
Larger mutual surplus receives a higher resolver-facing preference score.

When used with the reproduction `PreferenceOrder` resolver, the highest-scoring
non-conflicting mating proposals are resolved first. Because an organism cannot
participate in multiple resolved reproductive proposals in the same stage,
mating signal and choosiness can change realized parentage rather than merely
labeling candidate pairs.

## Mating-type-specific parental investment

`MatingTypeScaledInvestment` wraps another `ParentalInvestment` policy and scales
each parent's base contribution according to that parent's immutable mating
label. The scale is a rational numerator/denominator pair and uses deterministic
half-up rounding.

The reference ecology wraps the heritable `GeneticPhenotypeEnergyInvestment`.
For the default founder value `offspring_energy=4`:

```text
type_a scale 3/2 → 6 energy
type_b scale 1/2 → 2 energy
```

The historical pair total therefore remains eight energy units while reproductive
cost becomes asymmetric. The configuration can be changed or made symmetric.
Because the wrapper preserves the underlying policy's trait requirements,
`offspring_energy` remains heritable and still participates in engine preflight.

This creates an immediate fitness tradeoff: the higher-investment mating type can
lose more current energy per successful birth even when both parents contribute
to the same offspring. The reference values are integration defaults, not a
calibrated biological estimate.

## Mate-seeking movement

`PreferredMateTarget` extends the same mating policies into the movement system.
A target candidate must be individually reproductively eligible, behaviorally
allowed to reproduce, and accepted by the configured mating compatibility policy.

Viable mates are ranked by:

```text
highest mating preference
    ↓ tie
shortest spatial distance
    ↓ tie
lowest organism ID
```

This means sexual preference can influence movement before reproduction. An
organism may move toward a more preferred compatible mate even when another
acceptable mate is closer.

The reference ecology shares the same reproductive-eligibility, mating
compatibility, and mating-preference objects between movement and reproduction.
The two subsystems therefore cannot silently disagree about maturity, energy,
mating type, search range, choosiness, signal acceptance, or preference scoring.

## Search range versus mating radius

These spatial quantities have deliberately different meanings:

```text
mate_search_range
    → how far away a potential mate can be discovered and targeted

mating_radius
    → how close compatible parents must actually be to reproduce
```

Reference founders have `mate_search_range=3`, while `mating_radius=1`. A pair two
or three cells apart can therefore begin moving toward one another but cannot
reproduce until movement closes the distance.

## Composing mating rules

`AllOfMatingCompatibility` composes independent pair requirements:

```python
from evo_engine.reproduction import (
    AllOfMatingCompatibility,
    DifferentMatingTypes,
    MutualMateSearchRange,
    MutualSignalCompatibility,
)

compatibility = AllOfMatingCompatibility(
    compatibilities=(
        DifferentMatingTypes(),
        MutualMateSearchRange(),
        MutualSignalCompatibility(),
    )
)
```

The composite exposes the union of nested genetic trait requirements.
`PairwiseMating`, `PreferredMateTarget`, movement routing, and prioritized movement
intent propagate their collaborators' trait requirements. Engine preflight
therefore catches missing mating traits before the simulation begins.

Plain functions and lambdas remain valid `can_mate` and `preference_function`
collaborators for `PairwiseMating`. If an opaque callback reads genetic traits,
callers can continue declaring those dependencies manually through
`PairwiseMating.required_traits`.

## Reference ecology pipeline

The reference ecology activates mating type, search range, choosiness, mating
signal, and asymmetric parental investment:

```text
current organism state
    ↓
low energy?
    yes → food-seeking movement
    no  ↓
individually reproduction-ready?
    yes → reproduction-purpose movement
            ↓
        preferred compatible mate within mutual mate_search_range
            ↓
        targeted movement toward mate
    no  → exploration

later reproduction stage
    ↓
within mating_radius=1
    ↓
DifferentMatingTypes
    ↓
MutualMateSearchRange
    ↓
MutualSignalCompatibility
    ↓
MutualSignalMarginPreference
    ↓
PreferenceOrder resolver
    ↓
sexual inheritance, recombination, mutation, development
    ↓
mating-type-scaled parental energy contributions
    ↓
offspring mating-type assignment and birth
```

Founder signals exceed founder choosiness, so the initial population can mate.
Mutation and recombination can subsequently change search range, acceptance
thresholds, signal strength, and the heritable base offspring-energy investment,
thereby altering movement, realized parentage, and energetic reproductive cost.

## Current boundaries

The current sexual-selection model intentionally does not yet represent:

- explicit initiator/receiver or gamete-producing parent roles,
- genetically or environmentally determined mating type,
- sex chromosomes,
- mating-type-specific physiology beyond parental investment,
- imperfect detection of mates,
- separate energetic costs for courtship or signaling,
- memory of previously encountered mates,
- pair bonds or persistent mate choice, or
- mating systems in which one parent can participate in multiple successful
  reproductive events within the same stage.

Those are explicit model extensions rather than hidden assumptions in the current
reproduction process.
