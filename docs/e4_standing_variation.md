# E4 Standing Variation and Environment-Dependent Selection

E4 tests whether natural selection on known inherited locomotor variation moves
strategy frequencies in the direction predicted independently by E3.

The experiment is deliberately narrower than the richer B3 reference-ecology
flagship. It reuses E2's controlled clonal composition and E3's frozen ecological
performance environments without changing either model.

## Scientific question

E3 established, before focal variation was introduced, that `max_speed = 3`
outperforms both slower and faster strategies in the separated-resource corridor,
while the local-resource environment is speed-neutral.

E4 therefore asks:

> When speeds 1, 3, and 9 compete as standing inherited variation in the same
> controlled clonal ecology, does their committed population composition change in
> the direction predicted by E3?

The frozen prediction was:

- in the separated corridor, speed 3 should gain frequency and realized
  reproductive contribution relative to speeds 1 and 9;
- in the matched local-resource environment, the same strategies should show no
  consistent speed-ordered selective advantage.

A disagreement would have been treated as a scientific result rather than tuned
away.

## Frozen design

The canonical assay uses exactly three focal strategies:

```text
max_speed = 1, 3, 9
```

There is one founder per strategy, so each begins at frequency `1/3`. Mutation is
off. All three founders begin co-located at `(10, 15)`, which removes founder
position as a strategy-specific advantage.

All nonfocal biology and environmental quantities are inherited unchanged from
E3:

- `69 x 31` world;
- 30 committed steps;
- founder energy 100;
- body mass 1;
- resource request 10;
- reproduction threshold 140;
- reproduction investment 20;
- quadratic locomotion-use expenditure with coefficient 1;
- full assimilation;
- no metabolism, growth, aging, predation, renewable generation, mate search, or
  `max_speed` maintenance burden.

The environments are exactly E3's matched pair:

1. **local resource** — all 480 resource units at the founder coordinate;
2. **separated corridor** — four 120-unit deposits at `(22, 15)`, `(34, 15)`,
   `(46, 15)`, and `(58, 15)`.

The corridor remains axis-aligned so E2's known integer-grid bearing anisotropy is
not introduced as a new treatment confound.

## Founder-ID counterbalancing

E2 assigns founder IDs in caller order. Because permanent ID can influence event
ordering indirectly, E4 does not bind one speed permanently to one founder ID.

The canonical seed list cycles through three predeclared orders:

```text
A = (1, 3, 9)
B = (3, 9, 1)
C = (9, 1, 3)
```

Matched local/corridor runs use the same seed and same founder order. The nine
confirmation seeds therefore contain each speed-to-ID assignment exactly three
times.

A separate sanity assay compares canonical order `(1, 3, 9)` with reversed order
`(9, 3, 1)` on three predeclared seeds. This diagnostic changes only the
speed-to-founder-ID association.

## Evidence and replicate semantics

One complete simulation run/seed is one experimental replicate. Organisms within a
run are not independent replicates.

Primary evolutionary evidence comes from committed
`IndividualGeneticTraitRecorder(max_speed)` records. At every committed step E4
preserves:

- counts of speeds 1, 3, and 9;
- their frequencies when population size is nonzero;
- undefined frequencies if the whole population is extinct.

The primary endpoint is final-minus-initial focal frequency at committed step 30.
Population mean `max_speed` is not used as a substitute for the full polymorphic
composition.

Mechanism evidence remains separate from the evolutionary outcome:

- movement actor identity comes from same-step committed genetic-trait evidence;
- realized displacement and locomotion expenditure come through E1's applied
  movement measurement path;
- resource acquisition uses applied `ResourceConsumption.Event.amount` attributed
  to the same-step actor strategy;
- reproductive contribution counts applied reproduction events by offspring
  `max_speed`, cross-checked against the single clonal genetic parent;
- mutation remains off, and offspring are required to inherit the parent's focal
  strategy exactly.

The controlled E4 composition also validates the experiment-specific energy audit:

```text
3 * founder starting energy
+ total applied resource consumption
- total applied locomotion expenditure
= final living-population energy
```

This identity is a mechanics check for this minimal composition, not a universal
conservation statement for richer ecology.

## Discovery and freeze

Discovery seeds were predeclared as:

```text
7, 19, 31, 47, 73, 101
```

The first workflow attempt stopped before producing scientific output because the
new E4 consumer referenced the wrong E1 movement-measurement field name. That
implementation error was corrected without changing any biological or experimental
parameter.

The valid discovery matrix then produced a nondegenerate result without tuning:

- local resource: every run ended at counts `(4, 4, 4)` and frequencies
  `(1/3, 1/3, 1/3)`;
- separated corridor: every run ended at counts `(1, 4, 1)` and frequencies
  `(1/6, 2/3, 1/6)`.

The complete assay was therefore frozen unchanged before the confirmation seeds
were exposed.

## Independent confirmation

Confirmation used the disjoint predeclared seeds:

```text
5, 17, 29, 43, 61, 79, 97, 113, 137
```

All nine runs in each environment reached a defined endpoint; no run went extinct.

### Primary frequency result

| Environment | Speed 1 final frequency | Speed 3 final frequency | Speed 9 final frequency | Mean frequency changes `(1, 3, 9)` |
| --- | ---: | ---: | ---: | --- |
| Local resource | 0.333 | 0.333 | 0.333 | `(0.000, 0.000, 0.000)` |
| Separated corridor | 0.167 | 0.667 | 0.167 | `(-0.167, +0.333, -0.167)` |

The result is stronger than a treatment mean alone suggests. Every local-resource
confirmation replicate finished at counts `(4, 4, 4)`. Every separated-corridor
confirmation replicate finished at `(1, 4, 1)`, despite cycling the A/B/C
speed-to-founder-ID assignments.

The speed-3 final-frequency advantage over either focal alternative is therefore
`0.5` in every confirmed corridor replicate:

```text
2/3 - 1/6 = 1/2
```

### Mechanism evidence

Mean per-run mechanism evidence in confirmation was:

| Environment / speed | Births | Resource consumed | Realized distance | Locomotion expenditure |
| --- | ---: | ---: | ---: | ---: |
| Local / 1 | 3.000 | 156.667 | 0.000 | 0.000 |
| Local / 3 | 3.000 | 161.111 | 0.000 | 0.000 |
| Local / 9 | 3.000 | 162.222 | 0.000 | 0.000 |
| Corridor / 1 | 0.000 | 0.000 | 30.000 | 30.000 |
| Corridor / 3 | 3.000 | 290.000 | 55.667 | 167.000 |
| Corridor / 9 | 0.000 | 70.000 | 12.000 | 90.000 |

The local arm is evolutionarily neutral over the tested horizon even though
randomized scarce-resource allocation produces small strategy differences in
resource-consumption totals. Those allocation differences do not create a focal
frequency ranking: each strategy produces three births and ends at frequency
`1/3` in every confirmation run.

In the corridor, the evolutionary result follows the mechanism predicted by E3.
The speed-1 lineage travels but never reaches a productive reproductive state over
the horizon. The speed-9 lineage accesses some resource but pays a large locomotion
cost and also produces no offspring. The intermediate speed-3 lineage acquires most
of the resource and is the only focal lineage to produce offspring, causing its
frequency to rise from `1/3` to `2/3`.

These are mechanism observations in this controlled experiment, not a scalar
fitness score.

## Founder-order sanity check

Sanity seeds were predeclared as:

```text
17, 61, 113
```

For each seed, canonical order `(1, 3, 9)` and reversed order `(9, 3, 1)` produced
exactly the same corridor result:

- final counts `(1, 4, 1)`;
- final frequencies `(1/6, 2/3, 1/6)`;
- speed-3 frequency change `+1/3`;
- strategy-specific births, resource acquisition, realized distance, and locomotion
  expenditure identical between the two orders.

The tested founder-ID reversal therefore does not explain the E4 selection result.

## Prediction verdict

**E3's frozen prediction is supported.**

The independent confirmation demonstrates environment-dependent selection on
standing inherited locomotor variation in the controlled E2 ecology:

```text
local resource
    → no focal frequency change

separated resource corridor
    → speed 3 gains frequency
    → speeds 1 and 9 lose frequency
```

The result connects the independently characterized E3 ecological-performance
landscape to an actual change in inherited strategy composition without adding
mutation or a direct fitness variable.

## Claim boundaries

E4 supports a deliberately bounded claim:

> In this tested controlled clonal ecology, with the frozen E3 resource geometries,
> quadratic locomotion-use cost, finite 30-step horizon, and standing variation at
> speeds 1, 3, and 9, the separated corridor selects for the intermediate speed-3
> strategy while the local-resource environment is frequency-neutral.

E4 does **not** establish:

- a universal optimal locomotor speed;
- a species-calibrated biological prediction;
- that all patchy environments favor intermediate speed;
- mutation-driven adaptation or de novo evolution — mutation is off;
- perfect common-random-number synchronization between matched environment runs;
- long-run fixation or equilibrium from a 30-step experiment;
- that the small resource-allocation differences in the local arm constitute
  selection;
- a replacement or reinterpretation of B3's richer sexual reference-ecology result.

The richer B3 flagship and this controlled E2–E4 causal program are complementary
scientific demonstrations at different levels of model complexity.
