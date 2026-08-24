# Life-History Energy Strategy

The engine models low-energy behavior, reproductive eligibility, energetic cost,
and reserve preservation as separate decisions. Keeping these concerns separate
allows a simulation to represent different biological strategies without
hard-coding one global notion of "low energy."

## Decision layers

For a voluntary activity, the intended flow is:

```text
current organism state
        |
        v
1. behavior selection
   Should this purpose be attempted now?
        |
        v
2. activity-specific eligibility
   Is the organism biologically eligible?
        |
        v
3. cost / investment model
   How much energy would the action require?
        |
        v
4. expenditure policy
   May that cost be paid while respecting reserve strategy?
        |
        v
5. event
```

These layers answer different biological questions and should not be collapsed
into a single energy rule.

## Reusable energy thresholds

Many policies need an energy threshold. A threshold may be configured as a
literal integer:

```python
EnergyConservationBehavior(
    energy_threshold=10,
)
```

or as an organism-specific model:

```python
from evo_engine.energetics import DevelopmentalEnergyThreshold
from evo_engine.genetics import ENERGY_CONSERVATION_THRESHOLD

threshold = DevelopmentalEnergyThreshold(
    trait_name=ENERGY_CONSERVATION_THRESHOLD,
)

EnergyConservationBehavior(
    energy_threshold=threshold,
)
```

`DevelopmentalEnergyThreshold` reads the realized value from the organism's
`DevelopmentalProfile`, so genetic inheritance and developmental variation can
both contribute to the final strategy used by the organism.

The same threshold abstraction can be reused by movement intent, reproductive
minimum-energy eligibility, and dynamic reserve policies.

## Low-energy conservation behavior

`EnergyConservationBehavior` suppresses nonessential behavior below its resolved
threshold. By default, energy-acquisition and survival purposes remain allowed,
while somatic investment, reproduction, and exploration are suppressed.

Because the threshold is resolved from current organism state every time the
policy is queried, conservation mode is derived rather than stored. If feeding
raises energy above the threshold during an earlier stage, later stages can
naturally leave conservation mode during the same timestep.

`EnergyThresholdMovementIntent` may use the same threshold model. A low-energy
organism can therefore switch movement from exploration to energy acquisition,
while the behavior selector permits that survival-oriented movement and
suppresses discretionary behavior.

## Reproductive maturity and minimum energy

Reproduction eligibility may be composed with `AllOfEligibility`.

A life-history configuration can require both developmental maturity and a
minimum current-energy threshold:

```python
from evo_engine.energetics import DevelopmentalEnergyThreshold
from evo_engine.genetics import (
    REPRODUCTION_ENERGY_THRESHOLD,
)
from evo_engine.reproduction import (
    AllOfEligibility,
    DevelopmentalMaturityEligibility,
    MinimumEnergyEligibility,
)

eligibility = AllOfEligibility(
    eligibilities=(
        DevelopmentalMaturityEligibility(),
        MinimumEnergyEligibility(
            minimum_energy=DevelopmentalEnergyThreshold(
                trait_name=REPRODUCTION_ENERGY_THRESHOLD,
            ),
        ),
    ),
)
```

`DevelopmentalMaturityEligibility` defaults to the built-in `maturity_age`
trait. The organism is eligible only when its current age reaches its realized
developmental maturity target.

The energy threshold is a pre-attempt eligibility requirement. It is distinct
from the actual reproductive investment and from the reserve that must remain
after paying that investment.

## Dynamic post-expenditure reserve

`KeepFixedReserve` remains available for a simple fixed reserve.

`KeepEnergyReserve` accepts either a fixed integer or an energy-threshold model.
For an evolvable reserve:

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

A positive expenditure is allowed only when the organism can pay the complete
cost and still retain the resolved reserve. Zero-cost actions remain allowed
even when the organism is already below its desired reserve because they do not
cause further depletion.

Growth and Reproduction already accept energy-expenditure policies. Movement
now follows the same contract.

## Movement and starvation

Movement is voluntary expenditure. Its default `SpendToZero` policy allows an
affordable movement to reduce energy to exactly zero. A later Starvation stage
may then remove the organism.

The default policy does **not** allow movement whose full locomotion cost exceeds
current energy. This distinguishes:

```text
energy == cost
    -> action occurs
    -> energy becomes zero
    -> later starvation may occur

energy < cost
    -> action is not proposed
```

This makes locomotion consistent with Growth and Reproduction: voluntary
activities may consume the final available energy, but they may not complete an
action whose modeled cost cannot actually be paid.

Movement rechecks its expenditure policy immediately before application. If a
resolved event has become stale because another same-stage event changed energy,
application fails before position or energy is mutated.

## Example life-history strategy

A simulation can combine all of the layers:

```python
from evo_engine.behavior import (
    EnergyConservationBehavior,
    EnergyThresholdMovementIntent,
)
from evo_engine.energetics import (
    DevelopmentalEnergyThreshold,
    KeepEnergyReserve,
)
from evo_engine.genetics import (
    ENERGY_CONSERVATION_THRESHOLD,
    ENERGY_RESERVE,
    REPRODUCTION_ENERGY_THRESHOLD,
)
from evo_engine.reproduction import (
    AllOfEligibility,
    DevelopmentalMaturityEligibility,
    MinimumEnergyEligibility,
)

conservation_threshold = DevelopmentalEnergyThreshold(
    trait_name=ENERGY_CONSERVATION_THRESHOLD,
)
reserve_threshold = DevelopmentalEnergyThreshold(
    trait_name=ENERGY_RESERVE,
)

behavior = EnergyConservationBehavior(
    energy_threshold=conservation_threshold,
)

movement_intent = EnergyThresholdMovementIntent(
    energy_threshold=conservation_threshold,
)

reproductive_eligibility = AllOfEligibility(
    eligibilities=(
        DevelopmentalMaturityEligibility(),
        MinimumEnergyEligibility(
            minimum_energy=DevelopmentalEnergyThreshold(
                trait_name=REPRODUCTION_ENERGY_THRESHOLD,
            ),
        ),
    ),
)

reserve_policy = KeepEnergyReserve(
    minimum_energy=reserve_threshold,
)
```

This creates several independently evolvable or developmentally variable
life-history dimensions:

- the energy level at which conservation behavior begins;
- the age at reproductive maturity;
- the minimum current energy required to attempt reproduction;
- the reserve protected after voluntary expenditures.

Those traits can later participate in selection tradeoffs such as early versus
late maturity, aggressive versus conservative reproduction, and risky versus
reserve-preserving energy use.
