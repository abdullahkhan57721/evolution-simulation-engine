# Energy Expenditure Policies

Energy expenditure is modeled separately from behavioral selection, biological
eligibility, and energetic cost calculation.

```text
behavioral purpose / movement intent
    → why is the organism considering the action?
BehaviorSelectionModel
    → does the organism attempt that purpose now?
eligibility and domain rules
    → is the action biologically possible?
cost or investment model
    → how much energy would the action consume?
EnergyExpenditurePolicy
    → may that organism pay this particular cost?
event
```

This separation prevents a single energy threshold from carrying several
biologically different meanings.

## Public policies

`SpendToZero` permits a cost when current energy fully covers it, including a
payment that leaves exactly zero energy. A later mortality process such as
`Starvation` remains responsible for removing an organism that reaches zero.

`KeepFixedReserve` prevents a **positive** expenditure from lowering current
energy below a configured fixed reserve. Payment may leave exactly the reserve.
A zero-cost action is always permitted because it does not further deplete an
organism that may already be below the configured threshold.

`KeepEnergyReserve` provides the same reserve semantics but accepts either a
fixed integer or an organism-specific energy-threshold model. It is the policy
to use when reserve strategy should vary among organisms.

For example:

```text
current energy = 8
cost = 5
minimum reserve = 3
    → allowed
    → 3 remains

current energy = 7
cost = 5
minimum reserve = 3
    → rejected
```

## Growth

`Growth` defaults to `SpendToZero`. A simulation can instead configure a fixed
reserve:

```python
from evo_engine.energetics import KeepFixedReserve, LinearGrowthCost
from evo_engine.growth import FixedGrowthRate
from evo_engine.processes import Growth

process = Growth(
    growth_model=FixedGrowthRate(amount_per_timestep=1),
    growth_cost_model=LinearGrowthCost(energy_per_body_mass_unit=2),
    energy_expenditure_policy=KeepFixedReserve(minimum_energy=5),
)
```

Growth first determines potential gain, caps it at the developmental target,
prices the capped gain, and only then asks the expenditure policy whether the
organism may pay the resulting cost.

The policy is rechecked during event application. This protects reserves when
another same-stage event has consumed energy after Growth proposals were
created.

## Reproduction

`Reproduction` also defaults to `SpendToZero`. Its configured
`ParentalInvestment` determines each parent's proposed contribution, and the
same `EnergyExpenditurePolicy` is evaluated independently for every parent.

For example:

```python
from evo_engine.energetics import KeepFixedReserve
from evo_engine.processes import Reproduction

process = Reproduction(
    ...,
    energy_expenditure_policy=KeepFixedReserve(minimum_energy=10),
)
```

The policy is checked before a parent group becomes a proposal, again before
materialization performs inheritance/development/placement RNG, and again before
application charges any parent.

Application validates every contribution before charging any contribution, so a
stale multi-parent event cannot partially debit one parent and then fail on
another.

## Movement

`Movement` now uses the same expenditure contract as Growth and Reproduction.
Its default `SpendToZero` policy permits locomotion that can be fully paid,
including locomotion that leaves exactly zero energy, but rejects an attempted
movement whose full locomotion cost exceeds current energy.

A configured reserve policy is checked after displacement has been selected and
priced but before the movement event is recorded. It is checked again before
application mutates position or energy, so stale events fail atomically.

This means:

```text
current energy == locomotion cost
    → movement may occur
    → energy becomes zero
    → later Starvation may remove the organism

current energy < locomotion cost
    → movement is not proposed
```

## Reproductive eligibility is different

A pre-attempt eligibility rule and a post-payment reserve rule answer different
questions.

```text
current energy = 25
proposed reproductive investment = 10

MinimumEnergyEligibility(minimum_energy=20)
    → eligible because 25 >= 20
    → payment could leave 15

KeepFixedReserve(minimum_energy=20)
    → expenditure rejected because payment would leave only 15
```

Simulations may compose both when they represent distinct biological
constraints.

## Organism-specific reserve strategies

`DevelopmentalEnergyThreshold` reads a nonnegative integer threshold from an
organism's `DevelopmentalProfile`. Because developmental targets derive from the
genetic phenotype, this allows reserve strategies to be heritable while still
supporting developmental variation.

For example:

```python
from evo_engine.energetics import (
    DevelopmentalEnergyThreshold,
    KeepEnergyReserve,
)
from evo_engine.genetics import ENERGY_RESERVE

reserve_policy = KeepEnergyReserve(
    minimum_energy=DevelopmentalEnergyThreshold(
        trait_name=ENERGY_RESERVE,
    ),
)
```

Growth, Reproduction, and Movement all collect nested trait requirements from
their expenditure policies, so the simulation engine can validate the required
traits before step zero.

See **Life-History Energy Strategy** for the larger behavioral and reproductive
model built on these threshold and expenditure abstractions.
