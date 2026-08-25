# Explicit Physiological Tradeoffs

Performance traits should not all improve independently at zero cost. The
energetics layer therefore supports ongoing maintenance burdens for realized
physiological capabilities.

## Realized physiology, not raw alleles

`LinearTraitMaintenanceCost` reads values from each organism's
`DevelopmentalProfile`. Genetics still determines the inherited genetic
phenotype, while development determines the physiology actually realized by an
individual. This boundary matters for future plasticity and genotype-by-
environment effects: if development changes a realized capability, its energetic
maintenance burden changes with it.

A `TraitMaintenanceTerm` contributes

```text
max(0, realized_trait_value - baseline)
    * cost_numerator
    / cost_denominator
```

raw energy units per timestep. All terms are summed before integer rounding.
Several small burdens can therefore combine instead of each disappearing during
rounding.

Multiple terms may target the same trait. That makes piecewise-linear tradeoffs
possible. For example, one term can charge a modest cost from zero speed upward
while a second term begins above a high-speed threshold, producing increasing
marginal maintenance cost without changing the generic model.

## Composition with basal metabolism

`AdditiveMetabolicCost` composes independent metabolic-cost models. The
reference ecology uses two components:

1. body-mass-scaled basal metabolism, using the organism's heritable metabolic
   coefficient; and
2. realized physiological maintenance cost.

This preserves the distinction between the energetic cost of simply being an
organism of a given mass and the additional cost of maintaining expensive
performance machinery.

## Reference ecology defaults

`ReferencePhysiologicalTradeoffs` exposes the reference coefficients explicitly.
The default maintenance model covers:

- maximum speed,
- sensory range,
- sensory accuracy above a baseline,
- maximum intake rate,
- assimilation efficiency above a baseline,
- attack strength, and
- defense.

The defaults use hundredths of an energy unit per trait unit and are deliberately
illustrative rather than calibrated biological estimates. With the default
founder traits, these burdens sum to about 1.47 raw energy units and round to one
additional maintenance unit per timestep. Near the configured maxima of all
covered traits, they sum to about 6.6 raw units and round to seven.

The resulting selection pressure is explicit: higher performance may improve
resource acquisition, movement, predation, or survival, but it also increases
ongoing energy demand and therefore exposure to starvation and opportunity
costs elsewhere in the life history.

## Custom models

The mechanism is not restricted to the reference coefficients. Simulations can
supply any `LinearTraitMaintenanceCost` terms and combine that cost with other
`MetabolicCostModel` implementations through `AdditiveMetabolicCost`. Setting a
term's numerator to zero disables that tradeoff without changing the underlying
trait or genetic architecture.
