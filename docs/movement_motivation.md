# Movement Motivation and Targeting

Movement is modeled as a pipeline rather than a single random-walk decision. The
engine separates **why** an organism moves from **whether** that behavior is
allowed, **what** it targets, **how** it moves, and **whether it can pay** the
locomotion cost.

```text
current organism state
    ↓
MovementIntentModel
    → why move?
    ↓
BehaviorSelectionModel
    → may that purpose be attempted?
    ↓
MovementTargetModel
    → is there a target for that purpose?
    ↓
TargetedMovementModel or MovementPattern
    → what displacement is attempted?
    ↓
LocomotionCostModel + EnergyExpenditurePolicy
    → can the movement be paid?
    ↓
Movement event
```

This separation lets ecological motivations evolve without turning `Movement`
into a large conditional process.

## Prioritized movement intent

`PrioritizedMovementIntent` evaluates ordered `MovementIntentRule` objects and
returns the purpose associated with the first matching condition. Rules
short-circuit in tuple order.

```python
from evo_engine.behavior import (
    ENERGY_ACQUISITION,
    REPRODUCTION,
    EnergyBelowThresholdMovementCondition,
    MovementIntentRule,
    PrioritizedMovementIntent,
)

intent = PrioritizedMovementIntent(
    rules=(
        MovementIntentRule(
            behavioral_purpose=ENERGY_ACQUISITION,
            condition=EnergyBelowThresholdMovementCondition(
                energy_threshold=10,
            ),
        ),
        MovementIntentRule(
            behavioral_purpose=REPRODUCTION,
            condition=my_reproductive_condition,
        ),
    ),
)
```

If no rule matches, the default fallback purpose is `exploration`.

The rule order is part of the biological model. In the reference ecology:

```text
1. low energy          → energy acquisition
2. reproduction-ready  → reproduction
3. otherwise           → exploration
```

This implements a clear priority hierarchy: food acquisition overrides mate
seeking when energy is below the organism's conservation threshold.

`MovementIntentCondition` is structural. Custom conditions only need to provide:

```python
matches(organism, *, simulation_state) -> bool
```

Conditions may expose `required_traits`; those requirements propagate through
`MovementIntentRule`, `PrioritizedMovementIntent`, `Movement`, and engine
preflight.

## Reproductive readiness as movement motivation

The reproduction domain provides `ReproductiveEligibilityMovementCondition`.
It adapts any existing `ReproductiveEligibility` policy into the generic movement
condition interface.

The reference ecology reuses the exact same composed eligibility object for:

- deciding when reproduction becomes a movement motivation, and
- deciding whether an organism may enter the reproduction process.

This prevents movement and reproduction from drifting into two separate
interpretations of maturity or reproductive energy requirements.

## Purpose-routed targets

`PurposeMovementTargetRouter` maps behavioral purposes to independent target
models.

```text
energy_acquisition → resource targeting
reproduction       → mate targeting
exploration        → no target; use ordinary movement pattern
```

Each `PurposeTargetRoute` contains one purpose and one target model. Duplicate
purposes are rejected because target routing should be unambiguous. If no route
matches, the router defaults to `NoMovementTarget`, so `Movement` falls back to
its ordinary movement pattern.

Trait requirements from every routed target model are aggregated for engine
preflight.

## Mate-seeking movement

`PreferredMateTarget` is supplied by the reproduction domain and participates in
the generic target-routing interface.

A potential mate is considered only when it is:

1. a different organism,
2. individually reproductively eligible,
3. behaviorally allowed to reproduce in its current state, and
4. accepted by the configured mating compatibility policy.

Viable mates are ranked by:

```text
highest mating preference
    ↓ tie
shortest spatial distance
    ↓ tie
youngest organism ID
```

Preference therefore remains biologically meaningful during search. An organism
may move toward a more preferred mate rather than simply the nearest eligible
mate.

The reference ecology shares the same mating compatibility and preference
objects between `PreferredMateTarget` and `PairwiseMating`. Mate seeking and
actual mating therefore use identical `mate_search_range`, `choosiness`, and
`mating_signal` semantics.

## Search range versus mating radius

The reference ecology now distinguishes two spatial scales:

```text
mate_search_range = detection / targeting horizon
mating_radius     = physical proximity required for reproduction
```

Founders have `mate_search_range=3` and the reference `mating_radius=1`.
Organisms can therefore notice and approach compatible mates before they are
close enough to reproduce.

A pair outside both organisms' search ranges is not a mate-seeking target. Random
or otherwise motivated movement may eventually bring them into discovery range.
Once discovered, targeted movement can close the distance over one or more
steps.

## Interaction with behavior selection

Movement intent does not bypass the simulation's `BehaviorSelectionModel`.
`Movement` determines a purpose first and then asks behavior selection whether
that purpose is currently allowed.

This matters for low-energy conservation. Even if a custom intent model selected
`reproduction`, `EnergyConservationBehavior` can still suppress the attempt while
energy is low. The reference ecology additionally places the low-energy intent
rule first, so depleted organisms normally select food acquisition before that
second guard is needed.

## Current boundaries

The current system intentionally does not model:

- sex-specific or mating-type-specific movement roles,
- courtship costs separate from locomotion,
- imperfect detection of mates,
- memory of previously detected mates,
- territorial movement or migration priorities, or
- simultaneous optimization across many actions within one decision model.

Those features can be added by supplying new movement conditions, target models,
behavior-selection policies, or parent-selection policies without changing the
`Movement` process contract.
