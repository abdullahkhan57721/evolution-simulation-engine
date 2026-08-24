# Ecological Performance Traits

The engine separates **what an organism can perceive** from **what it can do after an interaction becomes possible**. This keeps sensory biology, predation biology, process timing, and conflict resolution independently configurable.

## Sensory range and accuracy

Resource-seeking movement can compose two independent perception models:

```text
sensory_range
    → which resource deposits are geometrically in range?

sensory_accuracy
    → which in-range deposits are actually detected?
```

`NearestResourceTarget` defaults to genetic `sensory_range` and fixed 100% sensory accuracy. The 100% default preserves the engine's historical deterministic targeting and consumes no additional random draws.

To make accuracy heritable, configure:

```python
from evo_engine.behavior import (
    GeneticPhenotypeSensoryAccuracy,
    NearestResourceTarget,
)

movement_target_model = NearestResourceTarget(
    sensory_accuracy_model=GeneticPhenotypeSensoryAccuracy(),
)
```

For each resource deposit inside sensory range, detection is sampled independently from the simulation RNG. Accuracy 0 always misses and accuracy 100 always detects without consuming an RNG draw.

The distinction creates different evolutionary tradeoffs. Increasing sensory range exposes more potential targets, while increasing sensory accuracy reduces false negatives among targets that are already close enough to sense.

## Predation eligibility

The reusable `evo_engine.predation` domain defines biological policies independently of the concrete `Predation` process.

The compatibility default is:

```text
LargerPredatorEligibility
    → predator current body mass > prey current body mass
```

The engine also provides:

```text
GeneticAttackDefenseEligibility
    → predator attack_strength > prey defense
```

These rules can be composed:

```python
from evo_engine.predation import (
    AllOfPredationEligibility,
    GeneticAttackDefenseEligibility,
    LargerPredatorEligibility,
)

eligibility = AllOfPredationEligibility(
    eligibilities=(
        LargerPredatorEligibility(),
        GeneticAttackDefenseEligibility(),
    )
)
```

This means body size and combat performance can evolve independently. A large organism is not automatically able to consume every smaller organism if its attack performance is insufficient.

## Predation preference

Feasibility and preference are separate questions:

```text
can_predate
    → may this predator-prey interaction occur?

preference_function
    → among feasible interactions, which should be considered first?
```

`GeneticAttackAdvantagePreference` scores a pairing as:

```text
predator attack_strength - prey defense
```

Higher scores are considered first by the predation `PreferenceOrder` resolver. Because each organism may participate in at most one resolved predation event per stage, preference affects both prey choice and conflict outcomes.

## Trait dependencies

Structured sensory and predation policies expose `required_traits`. Composite policies aggregate their nested dependencies automatically. The engine therefore validates required genetic traits before a simulation begins rather than failing deep inside a timestep.

Opaque custom callbacks remain supported. When a plain function or lambda reads traits, callers can still use the process's explicit `required_traits` field to declare dependencies manually.

## Reference ecology

The reference ecology activates all of these mechanisms. Its founder population carries:

| Trait | Default | Role |
| --- | ---: | --- |
| `sensory_range` | 4 | Radius in which resource deposits can potentially be sensed |
| `sensory_accuracy` | 90 | Percentage probability of detecting each in-range deposit |
| `attack_strength` | 8 | Predator performance against prey defense |
| `defense` | 5 | Resistance to predator attack |

Reference resource seeking uses genetic sensory range and accuracy. Reference predation requires both a current body-mass advantage and genetic attack greater than prey defense, then prefers the feasible interaction with the largest attack-defense margin.

These defaults are transparent integration values rather than calibrated biological claims.
