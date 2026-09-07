# E5 — Drift, Population Size, and Weak Selection

E5 asks when finite-population stochasticity can obscure or reverse the directional
selection established by E4.

The experiment is deliberately narrow. It reuses the E2 controlled clonal
locomotion composition, E1 scientific provenance/censoring semantics, and existing
pedigree evidence. It does **not** add a fitness field, modeled lineage state,
generic population-genetics framework, or new mortality mechanism.

## Scientific boundary

The evidence path is:

```text
controlled E2 simulation
        ↓
committed pedigree + individual max_speed evidence
        ↓
analysis-only founder ancestry labels
        ↓
complete A/B lineage composition through time
        ↓
run-level frequency / loss / fixation outcomes
        ↓
neutral stochastic baseline by founder count
        ↓
weak-selection comparison
```

One simulation run/seed is one independent replicate. Organisms within a run are
not independent replicates.

## Neutral ancestry without neutral phenotypes

Neutral A/B identity is assigned only to founder IDs in the experiment-analysis
layer. Descendants inherit the founder's analysis group by resolving the existing
single-parent clonal pedigree.

A/B is therefore **not**:

- a genetic locus;
- a phenotype or developmental characteristic;
- a reproductive role;
- an ecological parameter;
- a fitness value;
- simulation state.

In the neutral treatment every founder has `max_speed = 3` and otherwise identical
modeled biology. Reversing A/B labels leaves the simulation configuration unchanged.
This is stronger neutrality than introducing two nominal modeled phenotypes and
assuming they have no hidden ecological consequences.

## Frozen controlled design

E5 uses the E3 separated-resource corridor and canonical quadratic locomotion-use
cost. All founders are co-located. Mutation remains off.

The frozen founder-count regimes are:

```text
2, 8, 32
```

These are modeled founder/population-size regimes. They are **not** estimates of
real-world effective population size.

The fixed horizon is 60 committed steps.

Two balanced comparisons are run at each founder count:

1. **neutral:** A and B are both `max_speed = 3`;
2. **weak selection:** A is `max_speed = 3`, B is `max_speed = 4`.

Founder-ID assignment is counterbalanced by phase so an analysis label or favored
strategy is not permanently tied to one founder-ID parity.

### Resource correction during discovery

The first predeclared discovery composition used 160 resource units per founder.
That design produced exactly 50/50 lineage frequencies because every resource
patch divided into complete 10-unit feeding rounds; E2's randomized scarce-resource
allocation never became operative.

Before confirmation seeds were exposed, one bounded correction changed the resource
budget to **420 units per founder**. With four equal corridor deposits, each deposit
contains `105 × founder_count` resource units: ten complete feeding rounds plus one
half-population scarce round. This engages the already-existing unbiased
`RandomOrder` allocation without adding a new stochastic or biological mechanism.

No other biological or scenario parameter was tuned.

### Weak-selection pair freeze

E3 suggested neighboring speeds 3 and 4 as a small ecological-performance contrast.
After corrected discovery, the speed-3 shift at eight founders was approximately
one neutral standard deviation but no discovery replicate reversed direction.
Issue #156 therefore permitted exactly one bounded neighboring diagnostic: 3 vs 2.

That alternative was substantially stronger, not weaker. At eight founders its
mean speed-3 shift was about `+0.0801`, versus about `+0.0227` for 3 vs 4, and its
signal was about `3.69` neutral standard deviations rather than about `1.05`.
The 3-vs-2 alternative was rejected and **3 vs 4 was frozen** before independent
confirmation. No further strategy/scenario search occurred.

## Outcomes and censoring

For every replicate E5 records the complete committed A/B lineage trajectory and
separately derives:

- final lineage-frequency change;
- first A-lineage loss;
- first B-lineage loss;
- first fixation and fixation winner;
- whole-population extinction.

Loss, fixation, and extinction use E1's `FixedHorizonTimeToEvent`. If an event is
not observed by step 60 it is right-censored. E5 never assigns an unobserved event
to the terminal step.

Treatment summaries use simulation runs as the sample. Standard-library descriptive
statistics report the distribution of run-level frequency changes; no p-value or
generic inference framework is introduced.

## Independent confirmation

The frozen design was confirmed on 24 seeds disjoint from discovery. No replicate
was filtered or dropped.

### Neutral stochastic spread

| Founder count | Mean Δ A frequency | SD of Δ A frequency |
| ---: | ---: | ---: |
| 2 | +0.0099 | 0.0319 |
| 8 | -0.0015 | 0.0168 |
| 32 | -0.0003 | 0.0102 |

The neutral between-run spread contracts as founder count increases in this
controlled system. The experiment does not claim a universal population-size law;
it characterizes this finite-horizon modeled ecology.

### Weak 3-vs-4 selection

Speed 3 is the E3/E4-favored member of the pair in the separated corridor.

| Founder count | Mean Δ speed-3 frequency | Runs speed 3 increased | Runs speed 3 decreased | Absolute mean shift / neutral SD |
| ---: | ---: | ---: | ---: | ---: |
| 2 | +0.0215 | 13 / 24 | 2 / 24 | 0.67 |
| 8 | +0.0204 | 21 / 24 | 1 / 24 | 1.21 |
| 32 | +0.0221 | 24 / 24 | 0 / 24 | 2.17 |

The mean directional selection signal is similar across these founder-count
regimes, while neutral stochastic spread falls. Consequently:

- at two founders, stochastic spread is larger than the mean weak-selection shift
  and the favored strategy decreases in some independent runs;
- at eight founders, stochastic spread remains comparable to the selection signal
  and one independent run reverses direction;
- at 32 founders, the weak directional effect is more than two neutral standard
  deviations and all confirmation runs move in the favored direction.

E5 therefore demonstrates the distinction between **expected directional
selection** and the **realized outcome of one finite stochastic run**.

## Loss, fixation, and the controlled-composition boundary

No A/B lineage loss, fixation, or whole-population extinction was observed in the
confirmed equal-frequency E5 matrix. These outcomes are retained as right-censored,
not converted into terminal-step events.

A replicate-level audit also found no committed A- or B-lineage count decrease in
any confirmed neutral or weak-selection trajectory.

This is consistent with the deliberately minimal E2 composition:

```text
movement
  ↓
feeding
  ↓
clonal reproduction
  ↓
exact-zero starvation cleanup
```

There is no aging, metabolic maintenance, density-independent mortality, or other
turnover in this controlled assay. `SpendToZero` permits an action only when its
full energy cost is affordable, and reproduction transfers configured energy from
parent to offspring. Starvation removes only organisms that reach exactly zero
energy.

The absence of observed absorption is therefore part of the E5 result. It is not
evidence that stochasticity is absent: frequency variation and occasional reversal
of weak selection are directly observed. Nor does E5 claim that neutral lineages
cannot be lost in richer compositions or over other horizons.

## E6 rare-lineage handoff

E5 intentionally does **not** retrofit a `1 rare founder vs many founders` assay.
Such a treatment would start the rare lineage as a 100-energy founder in this
low-turnover composition. A future de-novo mutant may enter as a newborn or through
another introduction mechanism with different energy, age, location, and immediate
ecological exposure. Treating rare-founder persistence as the neutral loss
probability of a rare mutant would therefore be an unmatched control.

The E6 interpretation contract is:

```text
rare mutant disappeared
        ↓
compare with matched neutral rare-lineage control
        ↓
only then interpret selective versus stochastic loss
```

If E6 introduces a loss-capable rare lineage, it must include a neutral control
with the **same**:

- introduction mechanism and organism state;
- initial rarity;
- founder/population context;
- ecology and resource regime;
- horizon;
- evidence/censoring semantics.

That control should reuse E5's pedigree-derived ancestry and run-level
loss/fixation measurements. E5's observed frequency-noise distributions provide
the pre-invasion finite-population context, while E6's matched control must estimate
loss risk for the actual rare-lineage introduction state.

This preserves the core interpretation rule:

> disappearance of a rare lineage is not, by itself, evidence that the lineage was
> selectively disfavored.

## Claims and nonclaims

E5 supports the bounded claim that, in this controlled finite-horizon clonal
locomotion ecology, finite-population stochasticity can be comparable to weak
selection and can reverse the favored strategy's realized frequency direction in
individual runs, with stochastic spread decreasing across the tested founder-count
regimes.

E5 does **not** establish:

- real-world effective population sizes;
- a universal drift law or fixation probability;
- long-run stationary/fixation behavior;
- a scalar fitness model;
- a general population-genetics statistics framework;
- a neutral loss probability for a future mutant introduced in a different state;
- species-calibrated biological prediction.

The scientific value is the controlled distinction between deterministic-looking
selection pressure and finite-run stochastic evolutionary outcome, together with a
clear control requirement for later rare-lineage invasion experiments.
