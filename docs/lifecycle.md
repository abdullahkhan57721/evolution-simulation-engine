# Lifecycle and Age Mortality

The simulation architecture keeps **process behavior** separate from **timestep
ordering**. Individual processes do not decide when metabolism, movement,
reproduction, or mortality should occur. The domain-neutral
`SequentialStepCoordinator` owns ordered stage execution, while
`evo_engine.biology.build_standard_lifecycle()` provides one recommended
biological/ecological preset.

This keeps lifecycle assumptions configurable and outside the kernel. A
biological simulation can use the standard preset, omit optional stages, or
assemble a completely different sequence directly with
`SequentialStepCoordinator`.

## Standard lifecycle

The standard preset runs stages in this order:

```text
START OF TIMESTEP

1.  Starvation checkpoint
2.  Maximum-age mortality checkpoint
3.  Metabolism
4.  Starvation checkpoint
5.  Environment update          [optional]
6.  Movement                    [optional]
7.  Predation                   [optional]
8.  Resource consumption        [optional]
9.  Growth                      [optional]
10. Aging
11. Maximum-age mortality checkpoint
12. Reproduction                [optional]
13. Starvation checkpoint

END OF TIMESTEP
```

The biological factory accepts already-configured `StageCoordinator` instances.
It composes domain stages without changing the kernel's generic orchestration
machinery.

## Why the mortality checkpoints repeat

A checkpoint is intentionally separate from the process that changes the state
which can make an organism mortal.

### Starvation

The entry checkpoint prevents organisms already at zero energy from acting.
Metabolism then charges mandatory maintenance. The second checkpoint removes
organisms that could not survive maintenance before they receive movement,
feeding, growth, or reproductive opportunities.

A final checkpoint catches organisms that reach zero through later voluntary
energy expenditures. `SpendToZero` therefore means exactly what its name says:
a voluntary action may leave zero energy, but the organism can then starve at
the next mortality checkpoint.

### Maximum age

Maximum age also has two checkpoints.

The entry checkpoint prevents an organism that already satisfies
`age >= maximum_age` from beginning another timestep. This matters for loaded,
manually constructed, or otherwise externally initialized state.

The second checkpoint occurs immediately after Aging. It removes organisms that
have just reached their maximum age before they can reproduce or begin another
timestep.

## Exact age semantics

`Organism.age` means **completed simulation timesteps lived**.

For an organism with `maximum_age = 5`:

```text
birth / initial age       age = 0
after timestep 1          age = 1
after timestep 2          age = 2
after timestep 3          age = 3
after timestep 4          age = 4
after timestep 5          age = 5 → maximum-age death
```

The organism therefore completes five timesteps. It does not receive a sixth
turn.

Aging happens after growth and other within-timestep ecological activity, but
before reproduction at the end-of-step boundary. This ordering has two useful
consequences:

1. reproductive maturity is evaluated using the newly completed age at that
   boundary; and
2. offspring inserted by Reproduction arrive **after** Aging and remain age zero
   throughout their birth step.

Maximum-age mortality occurs between Aging and Reproduction, so a hard maximum
age remains hard: an organism that reaches its maximum age at the boundary does
not reproduce after reaching that limit.

## Maximum-age models

`MaximumAgeMortality` accepts a `MaximumAgeSource`, which can be either a plain
positive integer or a structural model.

Simple fixed lifespan:

```python
from evo_engine.processes import MaximumAgeMortality

mortality = MaximumAgeMortality(maximum_age=100)
```

The explicit fixed model is equivalent when a strategy object is preferable:

```python
from evo_engine.life_history import FixedMaximumAge
from evo_engine.processes import MaximumAgeMortality

mortality = MaximumAgeMortality(
    maximum_age=FixedMaximumAge(maximum_age=100),
)
```

The default is developmental and uses the canonical `MAXIMUM_AGE` trait:

```python
from evo_engine.processes import MaximumAgeMortality

mortality = MaximumAgeMortality()
```

Conceptually:

```text
Genome
   ↓
GeneticArchitecture
   ↓
GeneticPhenotype[MAXIMUM_AGE]
   ↓
DevelopmentalProfile[MAXIMUM_AGE]
   ↓
DevelopmentalMaximumAge
   ↓
MaximumAgeMortality
```

Because `DevelopmentalMaximumAge` declares its trait requirement,
`MaximumAgeMortality.required_traits` propagates `MAXIMUM_AGE` into the normal
biological preflight checks.

Custom simulations can also point `DevelopmentalMaximumAge` at another trait
name or provide any object with a compatible `determine_maximum_age()` method.
Returned maximum ages are validated at the shared boundary and must be positive
integers.

## Carcass semantics

Maximum-age death follows the same biomass rule as starvation: carcass resource
units come from the organism's **current body mass**, not its adult target.

This matters when organisms die before reaching adult size or when future
processes alter body mass during life.

## Constructing the preset

A minimal lifecycle can be assembled as follows:

```python
from evo_engine.biology import build_standard_lifecycle
from evo_engine.energetics import FixedMetabolicCost
from evo_engine.engine import StageCoordinator
from evo_engine.processes import Aging, MaximumAgeMortality, Metabolism, Starvation
from evo_engine.resolvers import AcceptAll

accept_all = AcceptAll()

starvation_stage = StageCoordinator(
    processes=(Starvation(),),
    resolver=accept_all,
)
maximum_age_stage = StageCoordinator(
    processes=(MaximumAgeMortality(maximum_age=100),),
    resolver=accept_all,
)
metabolism_stage = StageCoordinator(
    processes=(Metabolism(cost_model=FixedMetabolicCost(amount=1)),),
    resolver=accept_all,
)
aging_stage = StageCoordinator(
    processes=(Aging(),),
    resolver=accept_all,
)

step_coordinator = build_standard_lifecycle(
    starvation_stage=starvation_stage,
    maximum_age_mortality_stage=maximum_age_stage,
    metabolism_stage=metabolism_stage,
    aging_stage=aging_stage,
)
```

Ecological stages such as movement, predation, feeding, growth, and reproduction
can then be supplied as configured `StageCoordinator` instances. If an optional
stage is `None`, the factory simply omits it.

## Ordering is a modeling choice

`build_standard_lifecycle()` is deliberately a biological preset rather than an
invariant of `SimulationEngine`.

For example, a different model might represent seasonal reproduction before
somatic growth, environmental turnover after consumer activity, or probabilistic
senescence rather than a hard maximum age. Those alternatives should be
expressed by constructing a different ordered coordinator, not by adding
ordering branches to individual processes.
