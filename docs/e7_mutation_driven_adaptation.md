# E7 — Mutation-Driven Adaptation and Convergence

E7 asks a different question from E3–E6:

> If `max_speed` is not supplied as standing variation or an experimentally
> introduced rare strategy, can repeated focal mutation and clonal inheritance
> cause populations that begin below, near, and above the previously favored
> locomotor region to converge toward the same bounded trait distribution?

The answer in the frozen E7 assay is **no**. Independent confirmation rejects the
predeclared convergence criteria. The result is scientifically useful because it
shows that favorable ecological performance, selection on standing variation, and
bounded rare-lineage invasion are not sufficient to guarantee mutation-driven
convergence from distant starting conditions within a finite reproductive assay.

E7 remains above the frozen kernel and introduces no scalar fitness field,
adaptive-landscape optimizer, generic population-genetics/statistics layer, generic
mutation registry, or Workbench dependency.

## Scientific position in the controlled sequence

```text
E1 measurement / replicate semantics
        ↓
E2 controlled locomotion mechanics
        ↓
E3 monomorphic ecological performance
        ↓
E4 selection on standing inherited variation
        ↓
E5 finite-population stochasticity and weak selection
        ↓
E6 bounded reciprocal rare-lineage invasion
        ↓
E7 focal mutation, adaptation, and convergence
```

E3 identified speed 3 as the monomorphic performance maximum in the separated
corridor. E4 showed selection toward speed 3 when relevant strategies already exist
as standing inherited variation. E6 showed a bounded reciprocal asymmetry in which
a rare speed-3 lineage can reproduce against established speed-4 residents whereas
a rare speed-4 lineage does not reproduce against established speed-3 residents.

E7 therefore tests a harder accessibility question: can mutation itself generate
and propagate the sequence of inherited states needed for populations starting far
from that region to reach it?

## Narrow architecture change

Controlled locomotion previously installed `NoMutation` directly for its single
`MAX_SPEED` locus. E7 adds only the reusable seam required by this assay: the
controlled-locomotion spec builder can receive an optional focal
`MutationPolicy[int]` for `MAX_SPEED`. The default remains `NoMutation`, so existing
E2–E6 construction remains mutation-off.

The mutation path reuses existing genetics contracts:

```text
UniformIntegerMutation
        ↓
integer candidate
        ↓
IntegerAlleleDomain.constrain
        ↓
Locus.validate
        ↓
legal inherited max_speed
```

No new mutation framework is introduced. The existing legal controlled-locomotion
speed domain remains `0..20`; this is deliberately wider than the E3–E6 reference
region `2..4`. Existing integer-domain clamping remains the boundary semantic.
Consequently, accumulation at speed 0 or 20 is measured explicitly and is never
interpreted as evidence of an optimum.

## Frozen final assay

Each E7 replicate uses the E3 separated-resource corridor with nonfocal E2 biology
unchanged:

- world size `69 x 31`;
- 8 monomorphic founders co-located at `(10, 15)`;
- founder energy `100` and body mass `1`;
- 420 resource units per founder, or 3360 total, split across the four E3 corridor
  deposits;
- resource request `10`;
- reproduction threshold `140` and offspring investment `20`;
- canonical quadratic locomotion-use cost with coefficient `1`;
- no metabolism, growth, aging, predation, renewable resource generation, or mate
  search;
- fixed horizon of 60 committed steps.

Three independent monomorphic starting conditions are predeclared:

```text
low:   max_speed = 1
near:  max_speed = 3
high:  max_speed = 7
```

Only the haploid `MAX_SPEED` locus mutates. The final frozen mutation policy is:

```text
UniformIntegerMutation(
    probability_ppm=1_000_000,
    max_change=1,
)
```

Thus every clonal birth receives exactly one attempted focal `-1` or `+1` mutation,
subject only to the existing legal-domain constraint. The 100% assay rate is not a
species-calibrated biological mutation rate; it is an intentionally high finite-
horizon mutation-supply treatment established during bounded discovery.

## Evidence and replicate semantics

One simulation run/seed remains one stochastic replicate. Organisms within a run
are dependent observations and are never pooled as independent replicates.

Every committed state from step 0 through step 60 retains the complete legal-domain
`max_speed` distribution for speeds `0..20`, not just a mean. E7 derives:

- counts and frequencies across the full focal domain;
- population mean and median as secondary location summaries;
- population mass in the reference region `2..4`;
- modal speeds and occupied support;
- boundary occupancy at speeds 0 and 20;
- population size, energy, and remaining resources;
- parent-to-offspring focal transitions from committed pedigree plus trait evidence;
- realized movement, locomotion energy expenditure, resource acquisition, and
  reproductive contribution by inherited speed;
- whole-population extinction with E1 fixed-horizon event semantics.

A realized parent-to-offspring focal change is inferred only when pedigree and
committed genetic-trait evidence agree. E7 fails loudly if the clonal one-parent or
bounded-step assumptions are violated.

## Discovery and the single bounded adjustment

The original candidate design used a 10% focal mutation probability with the same
`±1` effect. Six predeclared discovery seeds were run for all three starts:

`(13, 31, 47, 73, 101, 127)`

That assay supplied only about three realized focal changes per run on average and
could not meaningfully test a multi-step path such as `7 → 6 → 5 → 4`. Issue #176
had predeclared at most one bounded protocol adjustment if discovery was technically
degenerate.

E7 used that allowance only to increase mutation probability from 10% to 100%.
Starting speeds, mutation step size, speed domain, resource scale, horizon, corridor
geometry, locomotion cost law, and all nonfocal biology remained unchanged.

The adjusted discovery supplied abundant focal mutation:

| Start | Mean endpoint speed | Mean mass in 2..4 | Mean boundary mass | Mean realized changes |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 1.3111 | 0.3687 | 0.2434 | 44.833 |
| 3 | 3.1400 | 1.0000 | 0.0000 | 38.333 |
| 7 | 7.1029 | 0.0000 | 0.0000 | 28.000 |

Discovery therefore showed that mutation supply was no longer the main limitation,
but the three starting conditions still produced strongly different endpoint
distributions. That was sufficient to freeze the assay and define confirmation
criteria without further tuning.

## Frozen convergence criteria

Before any confirmation seed was executed, Issue #176 froze the following criteria.
All must pass to classify E7 as convergent.

For each starting condition, at least 18 of 24 confirmation runs must satisfy:

1. **directional or bounded location**
   - start 1: endpoint median at least 2;
   - start 3: endpoint median in `2..4`;
   - start 7: endpoint median at most 4;
2. **reference-region occupancy**: at least 50% of the endpoint population lies in
   speeds `2..4`;
3. **boundary diagnostic**: combined endpoint mass at speeds 0 and 20 is at most
   10%;
4. **nonextinction**: the population remains defined at the fixed horizon.

In addition, every pair of equal-run-weighted endpoint distributions must have
simple full-domain overlap of at least 0.50:

```text
sum(min(p_i, q_i))  for speeds i = 0..20
```

Extinction counts against run-level criteria rather than being filtered. The
criteria were not revised after confirmation outcomes were observed.

## Independent confirmation

Confirmation used 24 fresh seeds, disjoint from discovery:

`(677, 683, 691, 701, 709, 719, 727, 733, 739, 743, 751, 757, 761, 769, 773, 787, 797, 809, 811, 821, 823, 827, 829, 839)`

No replicate was filtered.

### Endpoint summaries

| Start | Mean endpoint speed | Mean mass in 2..4 | Mean boundary mass | Mean realized changes |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 1.1611 | 0.3298 | 0.3373 | 45.542 |
| 3 | 3.0959 | 1.0000 | 0.0000 | 38.083 |
| 7 | 6.9915 | 0.0000 | 0.0000 | 27.792 |

All 72 populations remained nonextinct through committed step 60.

### Frozen-criterion results

| Start | Directional / bounded | Majority in 2..4 | Boundary ≤ 0.10 | Nonextinct |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 0/24 | 0/24 | 0/24 | 24/24 |
| 3 | 24/24 | 24/24 | 24/24 | 24/24 |
| 7 | 0/24 | 0/24 | 24/24 | 24/24 |

Equal-run endpoint-distribution overlap was:

- start 1 versus start 3: `0.3298`;
- start 1 versus start 7: `0.0000`;
- start 3 versus start 7: `0.0000`.

The frozen convergence classification is therefore **false**.

## Mechanism evidence

The negative result is not explained by a failure to generate mutations.
Confirmation shows different reproductive accessibility from each starting state.

### Start 1

The principal realized focal transitions were:

- `1 → 0`: 380 offspring;
- `1 → 2`: 337 offspring;
- `2 → 1`: 185 offspring;
- `2 → 3`: 191 offspring.

Speed-2 descendants therefore made real reproductive contributions and generated
speed-3 descendants. Upward evolutionary movement was biologically reachable from
the low start.

At the same time, substantial population mass accumulated at speed 0. Speed-0
organisms incur no locomotion-use cost because they do not move, yet they can remain
present and consume local resources. The mean endpoint boundary mass was 0.3373,
and no confirmation replicate met the frozen ≤0.10 boundary diagnostic. This is a
boundary effect of the configured assay, not evidence that speed 0 is an adaptive
optimum.

### Start 3

The dominant realized transitions were:

- `3 → 2`: 468 offspring;
- `3 → 4`: 446 offspring.

All recorded reproductive contribution came from speed-3 parents; speed-2 and
speed-4 descendants did not themselves reproduce within the horizon. The resulting
endpoint populations nevertheless stayed entirely inside the reference region
`2..4` in all 24 runs.

This is bounded start-dependent variation under the high-mutation assay. It does not
by itself establish a stationary mutation-selection equilibrium.

### Start 7

The realized transitions were:

- `7 → 6`: 337 offspring;
- `7 → 8`: 330 offspring.

All 667 recorded births were produced by speed-7 parents. Speed-6 and speed-8
descendants produced **zero** offspring in confirmation. Thus mutation repeatedly
created the first neighboring states, but the descendants did not propagate a
second mutational step toward speed 5, 4, or 3 within the finite assay.

The high-start result therefore reflects a reproductive-propagation bottleneck, not
insufficient first-step mutation supply.

## Interpretation

E7 independently confirms **non-convergence** in this particular controlled
finite-horizon clonal assay.

The result sharpens the causal story established by E3–E6:

```text
favorable ecological performance
        ≠
selection can act on supplied standing variation
        ≠
a rare supplied strategy can invade
        ≠
mutation-driven populations must reach that strategy
```

E3–E6 characterize what happens when relevant locomotor strategies are already
present. E7 demonstrates that evolutionary accessibility also depends on whether
intermediate descendants reproduce enough to generate subsequent inherited steps.
The high-start lineage does not traverse the required chain, while the low-start
lineage can move upward through speed 2 but simultaneously experiences strong lower-
boundary accumulation.

The endpoint distributions are therefore strongly **start-dependent** rather than
convergent. Start 3 remains bounded in `2..4`; start 1 produces a mixture concentrated
around `0..3` with substantial boundary mass; start 7 remains confined to `6..8`.

## What E7 does not establish

E7 does not establish:

- a universal optimal speed;
- a formal mutation-selection balance or evolutionary equilibrium;
- long-run convergence or divergence beyond the 60-step horizon;
- species-calibrated mutation rates;
- asymptotic adaptive dynamics;
- a general fitness landscape;
- that the speed-0 boundary accumulation is biologically favorable outside this
  configured assay;
- that longer horizons, different reproduction/resource regimes, or richer genetics
  would reproduce the same accessibility constraints.

Those are separate experimental questions and must not be answered by post-hoc
retuning of E7.

## Architectural outcome and handoff

E7 demonstrates that the existing typed mutation/domain contracts are sufficient for
a rigorous focal mutation experiment. The only reusable composition change earned
by the milestone is the optional focal mutation-policy seam in controlled
locomotion; default mutation-off behavior remains intact for E2–E6.

The controlled E1–E7 sequence now forms a complete first causal program from
measurement semantics through mechanics, performance, standing-variation selection,
finite-population stochasticity, rare-lineage invasion, and mutation-driven
accessibility.

A future controlled-science milestone should start from a new predeclared question
rather than modifying E7 until convergence appears. Possible future pressure may
concern longer generational turnover, richer reproductive opportunity, more complex
genetic architecture, or changing ecology, but those are new experiments with new
scientific identities rather than corrections to this confirmed negative result.
