# Mate Choice and Sexual Selection

The reproduction domain separates four questions that are often conflated in a simple mating model:

```text
individual reproductive eligibility
    → may this organism reproduce at all?

hard spatial opportunity
    → are the organisms inside the configured mating neighborhood?

mating compatibility
    → can these two organisms discover and accept one another?

pair preference
    → among compatible pairs, which pairing is favored when proposals conflict?
```

This separation allows life history, spatial ecology, mate search, sexual selection, and reproduction conflict resolution to evolve independently.

## Role-symmetric first model

The engine currently treats two reproductive parents as interchangeable. It does not yet model sexes, mating types, or role-specific courtship. The built-in sexual-selection policies therefore use symmetric rules: swapping the first and second parent does not change whether the pair is compatible or how it is scored.

That is a deliberate first model, not a claim that biological mating systems are generally symmetric. Future parent-selection implementations can introduce role-specific behavior without changing the inheritance or reproduction-event contracts.

## Mate search range

`MutualMateSearchRange` reads each organism's genetic `mate_search_range` and measures pair distance with a configurable spatial metric. The default metric is direct-grid Chebyshev distance.

A pair is discoverable only when:

```text
pair distance <= first parent's mate_search_range
and
pair distance <= second parent's mate_search_range
```

The rule is mutual because current parent roles are interchangeable. A future initiator/receiver or signaling model could instead use asymmetric encounter rules.

The `PairwiseMating.neighborhood` remains a hard geometric cap applied first. This preserves the existing API and allows simulations to impose a maximum interaction scale independently of organism traits. The reference ecology uses a broad hard cap so genetic mate-search range supplies the meaningful local limit.

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

Equality is sufficient. Increasing mating signal can therefore increase mating opportunities, while increasing choosiness can reject more potential mates.

## Pair preference

Compatibility answers whether a pair is possible. Preference answers which compatible pair should win when an organism has multiple candidates.

`MutualSignalMarginPreference` scores the total surplus above both acceptance thresholds:

```text
(second signal - first choosiness)
+
(first signal - second choosiness)
```

The score is symmetric. A pair exactly meeting both thresholds receives zero. Larger mutual surplus receives a higher resolver-facing preference score.

When used with the reproduction `PreferenceOrder` resolver, the highest-scoring non-conflicting mating proposals are resolved first. Because an organism cannot participate in multiple resolved reproductive proposals in the same stage, mating signal and choosiness can change realized parentage rather than merely labeling candidate pairs.

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

The composite exposes the union of nested genetic trait requirements. `PairwiseMating` also aggregates requirements from its compatibility and preference collaborators. Engine preflight therefore catches missing mating traits before the simulation begins.

Plain functions and lambdas remain valid `can_mate` and `preference_function` collaborators. If an opaque callback reads genetic traits, callers can continue declaring those dependencies manually through `PairwiseMating.required_traits`.

## Reference ecology

The reference ecology activates all three built-in mating traits:

| Trait | Default | Role |
| --- | ---: | --- |
| `mate_search_range` | 3 | Maximum Chebyshev distance each parent can use to discover the other |
| `choosiness` | 5 | Minimum partner signal accepted |
| `mating_signal` | 8 | Signal presented to potential mates |

Its mating pipeline is:

```text
individually mature and energetic parents
    ↓
within hard mating neighborhood
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

Founder signals exceed founder choosiness, so the initial population can mate. Mutation and recombination can subsequently change search range, acceptance thresholds, and signal strength and thereby alter realized reproductive success.

## Current boundary

This milestone models mate encounter and choice at the reproduction stage. It does **not** yet make organisms move toward potential mates. Active mate-seeking movement is a separate behavioral problem because it requires deciding when reproduction should become the purpose of movement, how potential mates are perceived before reproduction, and how that motivation competes with food seeking and exploration.

Keeping that future behavior separate avoids making `PairwiseMating` responsible for movement or turning movement into a hidden side effect of reproduction.
