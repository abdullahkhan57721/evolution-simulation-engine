# Mate Choice and Sexual Selection

The reproduction domain separates four questions that are often conflated in a
simple mating model:

```text
individual reproductive eligibility
    → may this organism reproduce at all?

mate discovery
    → can these organisms detect one another as potential mates?

mating compatibility
    → do both organisms accept the pairing?

pair preference
    → among compatible pairs, which pairing is favored when proposals conflict?
```

The movement system adds a fifth, separate question:

```text
mate-seeking movement
    → should an organism move toward a viable potential mate before mating?
```

Keeping these questions separate allows life history, spatial ecology, mate search,
sexual selection, behavior, and reproduction conflict resolution to evolve
independently.

## Role-symmetric first model

The engine currently treats two reproductive parents as interchangeable. It does
not yet model sexes, mating types, or role-specific courtship. The built-in
sexual-selection policies therefore use symmetric rules: swapping the first and
second parent does not change whether the pair is compatible or how it is scored.

That is a deliberate first model, not a claim that biological mating systems are
generally symmetric. Future parent-selection implementations can introduce
role-specific behavior without changing the inheritance or reproduction-event
contracts.

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

The rule is mutual because current parent roles are interchangeable. A future
initiator/receiver or signaling model could instead use asymmetric encounter
rules.

The reference ecology now treats `mate_search_range` as a **detection and
mate-targeting horizon**, not as the distance at which reproduction itself can
occur. Organisms may detect a compatible mate several cells away, move toward that
mate, and reproduce only after reaching the configured close-range
`mating_radius`.

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

This means sexual preference can influence **movement before reproduction**.
An organism may move toward a more preferred compatible mate even when another
acceptable mate is closer.

The reference ecology shares the same reproductive-eligibility, mating
compatibility, and mating-preference objects between movement and reproduction.
The two subsystems therefore cannot silently disagree about maturity, energy,
search range, choosiness, signal acceptance, or preference scoring.

## Search range versus mating radius

These spatial quantities now have deliberately different meanings:

```text
mate_search_range
    → how far away a potential mate can be discovered and targeted

mating_radius
    → how close compatible parents must actually be to reproduce
```

Reference founders have `mate_search_range=3`, while `mating_radius=1`.
A pair two or three cells apart can therefore begin moving toward one another but
cannot reproduce until movement closes the distance.

This restores the hard `PairwiseMating.neighborhood` to a physical interaction
constraint rather than using it as a broad discovery cap.

## Composing mating rules

`AllOfMatingCompatibility` composes independent pair requirements:

```python
from evo_engine.reproduction import (
    AllOfMatingCompatibility,
    MutualMateSearchRange,
    MutualSignalCompatibility,
)

compatibility = AllOfMatingCompatibility(
    compatibilities=(
        MutualMateSearchRange(),
        MutualSignalCompatibility(),
    )
)
```

The composite exposes the union of nested genetic trait requirements.
`PairwiseMating`, `PreferredMateTarget`, movement routing, and prioritized movement
intent all propagate their collaborators' trait requirements. Engine preflight
therefore catches missing mating traits before the simulation begins.

Plain functions and lambdas remain valid `can_mate` and `preference_function`
collaborators for `PairwiseMating`. If an opaque callback reads genetic traits,
callers can continue declaring those dependencies manually through
`PairwiseMating.required_traits`.

## Reference ecology

The reference ecology activates all three built-in mating traits:

| Trait | Default | Role |
| --- | ---: | --- |
| `mate_search_range` | 3 | Maximum Chebyshev distance for mutual mate discovery |
| `choosiness` | 5 | Minimum partner signal accepted |
| `mating_signal` | 8 | Signal presented to potential mates |

Its combined behavior and reproduction pipeline is:

```text
current organism state
    ↓
low energy?
    yes → food-seeking movement
    no  ↓
individually reproduction-ready?
    yes → reproduction-purpose movement
            ↓
        preferred viable mate within mutual mate_search_range
            ↓
        targeted movement toward mate
    no  → exploration

later reproduction stage
    ↓
within mating_radius=1
    ↓
MutualMateSearchRange
    ↓
MutualSignalCompatibility
    ↓
MutualSignalMarginPreference
    ↓
PreferenceOrder resolver
    ↓
sexual inheritance, recombination, mutation, development, birth
```

Founder signals exceed founder choosiness, so the initial population can mate.
Mutation and recombination can subsequently change search range, acceptance
thresholds, and signal strength and thereby alter both movement trajectories and
realized reproductive success.

## Current boundaries

The current sexual-selection model intentionally does not yet represent:

- sexes, mating types, or role-specific courtship,
- imperfect detection of mates,
- separate energetic costs for courtship or signaling,
- memory of previously encountered mates,
- pair bonds or persistent mate choice, or
- mating systems in which one parent can participate in multiple successful
  reproductive events within the same stage.

Those are explicit model extensions rather than hidden assumptions in the current
reproduction process.
