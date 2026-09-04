# E3 Ecological Performance Landscape

E3 asks a deliberately pre-evolutionary question:

> Before focal evolution is allowed, how does inherited `max_speed` capacity affect ecological performance in the controlled E2 locomotion system?

The experiment preserves the scientific dependency chain:

```text
inherited max_speed capacity
        ↓
realized movement
        ↓
locomotion expenditure
        ↓
resource acquisition
        ↓
population energy
        ↓
fixed-horizon reproduction / survival
```

No scalar fitness score is introduced. One complete simulation run/seed is one replicate; organisms inside a run are dependent observations rather than additional replicates.

## Controlled system

E3 reuses the E2 controlled clonal locomotion composition without changing its biology or the frozen kernel. The focal inherited trait is monomorphic `max_speed`; `NoMutation` remains installed. Nonfocal biology is fixed.

The canonical assay uses:

- `max_speed` grid `1..10`;
- one founder at `(10, 15)` in a `69 × 31` world;
- fixed 30-step horizon;
- founder energy `100`;
- body mass `1`;
- resource request amount `10`;
- reproduction threshold `140`;
- reproduction investment `20`;
- quadratic locomotion-use cost with coefficient `1`;
- full assimilation;
- no metabolism, growth, aging, predation, renewable resource generation, mate search, focal mutation, or `max_speed` maintenance penalty.

The E2 public domain permits `max_speed` through `20`, so the E3 grid ending at `10` does not force an observed optimum to coincide with the trait-domain ceiling.

## Resource environments

Both canonical environments begin with exactly 480 resource units.

### Local-resource null

All 480 units begin at the founder coordinate `(10, 15)`. No travel is required for access. This treatment is intended to test whether `max_speed` has any ecological effect when locomotor access provides no benefit.

### Separated corridor

Four equal 120-unit deposits begin at:

```text
(22, 15)
(34, 15)
(46, 15)
(58, 15)
```

The corridor is axis-aligned and kept well inside the world boundary. This controls the integer-grid bearing anisotropy already measured by E2 rather than smoothing it away. Canonical E3 runs fail loudly if attempted and committed movement distances diverge unexpectedly.

## Evidence and outcomes

E3 derives all measurements from authoritative committed evidence:

- E1 movement measurement provides applied movement count, attempted/realized displacement, and locomotion-energy expenditure;
- applied `ResourceConsumption.Event.amount` provides total acquired/consumed resource;
- committed population observations provide the population-energy trajectory and final population state;
- applied `Reproduction.Event` count provides fixed-horizon cumulative births;
- first observed zero population defines fixed-horizon extinction timing, otherwise extinction is right-censored at the horizon.

The primary ecological-performance outcome is **cumulative applied reproduction events / births per run at the fixed horizon**. This is a replicate-level outcome, not a pooled per-organism reproductive rate.

## Controlled energy accounting

Because this composition has full assimilation and omits basal metabolism, growth, and aging, while reproduction transfers invested energy from parent to offspring, the canonical assay supports the experiment-specific identity:

```text
initial founder energy
+ total applied resource consumption
- total applied locomotion energy expenditure
= final total living-organism energy
```

Every E3 replicate checks this identity exactly. This is a mechanics audit of the controlled composition, not a universal conservation law for the richer reference ecology.

## Discovery and freeze

The predeclared discovery seeds were:

```text
3, 11, 23
```

No parameter search or calibration was required. The local-resource arm was exactly speed-neutral: every speed `1..10` produced six births in every discovery replicate, consumed all 480 resources, realized no movement, and incurred no locomotion cost.

The separated-corridor discovery means were:

| `max_speed` | Mean births |
| ---: | ---: |
| 1 | 2.000 |
| 2 | 3.333 |
| 3 | **4.000** |
| 4 | 3.333 |
| 5 | 3.000 |
| 6 | 2.333 |
| 7 | 2.333 |
| 8 | 2.000 |
| 9 | 1.000 |
| 10 | 0.000 |

The assay was therefore frozen unchanged before confirmation.

## Independent confirmation

The disjoint confirmation seeds were:

```text
17, 29, 41, 53, 67, 79, 97, 109
```

No confirmation replicate was filtered or discarded.

The local-resource null again produced exactly six births for every speed in all eight confirmation replicates, with all resources consumed, zero movement, zero locomotion expenditure, and no extinction.

The separated-corridor confirmation landscape was:

| `max_speed` | Mean births | Births by confirmation seed | Mean resource consumed | Mean realized distance | Mean locomotion energy | Extinctions |
| ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 1 | 2.000 | 2,2,2,2,2,2,2,2 | 120.00 | 42.0 | 42.0 | 0/8 |
| 2 | 3.625 | 4,4,3,4,4,3,3,4 | 247.50 | 86.0 | 172.0 | 0/8 |
| 3 | **4.000** | 4,4,4,4,4,4,4,4 | 340.00 | 72.0 | 216.0 | 0/8 |
| 4 | 3.750 | 4,4,4,4,3,4,4,3 | 286.25 | 57.5 | 230.0 | 0/8 |
| 5 | 3.000 | 3,3,3,3,3,3,3,3 | 280.00 | 52.25 | 243.25 | 0/8 |
| 6 | 2.750 | 3,3,3,3,2,3,3,2 | 280.00 | 37.5 | 225.0 | 0/8 |
| 7 | 2.750 | 3,3,3,3,2,3,3,2 | 280.00 | 36.0 | 222.0 | 0/8 |
| 8 | 2.000 | 2,2,2,2,2,2,2,2 | 280.00 | 36.0 | 240.0 | 0/8 |
| 9 | 1.000 | 1,1,1,1,1,1,1,1 | 280.00 | 36.0 | 270.0 | 0/8 |
| 10 | 0.000 | 0,0,0,0,0,0,0,0 | 0.00 | 10.0 | 100.0 | 8/8 |

The independently highest mean fixed-horizon reproductive output is at `max_speed = 3`. The curve is not monotonic: low capacity limits timely access to separated resources, whereas high capacity becomes increasingly expensive under the quadratic use-cost rule. At speed 10 the founder spends its entire 100-unit starting energy on the first 10-cell move, reaches no resource, and becomes extinct in every confirmation run.

This result is bounded to the tested controlled composition. It does not establish a universal optimal speed.

## Mechanism sensitivity: remove locomotion cost

A predeclared bounded sensitivity retained the separated corridor and changed only locomotion-cost coefficient `1 → 0`. The sensitivity seeds were:

```text
17, 41, 67, 97
```

With canonical cost, this subset reproduced the interior peak and high-speed penalty. With zero locomotion cost:

| `max_speed` | Mean births | Mean resource consumed | Mean locomotion energy | Extinctions |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 2.50 | 120 | 0 | 0/4 |
| 2 | 5.00 | 360 | 0 | 0/4 |
| 3 | 6.00 | 480 | 0 | 0/4 |
| 4–10 | 6.25 | 480 | 0 | 0/4 |

Removing locomotion expenditure removes the canonical high-speed penalty: speeds 3–10 reach all resources, and speeds 4–10 form a near-flat high-performance plateau. Most sharply, speed 10 changes from zero births and extinction in 4/4 canonical sensitivity runs to 6.25 mean births and no extinction with zero cost.

This supports the proposed mechanism rather than merely describing the performance curve: locomotor capacity creates a resource-access benefit, while quadratic locomotion-use expenditure creates the high-speed cost that produces the canonical interior optimum.

## Frozen E4 prediction

E4 should introduce standing inherited variation while keeping mutation off and counterbalancing founder positions/labels. E3 freezes the following directional prediction before E4 begins:

> **In the frozen separated-corridor environment with canonical quadratic locomotion cost, standing variation containing a slow strategy (`max_speed = 1`), the independently favored intermediate strategy (`max_speed = 3`), and a fast costly strategy (`max_speed = 9`) should shift toward the intermediate speed-3 lineage across replicate-level outcomes. Speed 3 should show greater realized reproductive contribution and a positive frequency change relative to speeds 1 and 9. In the matched local-resource environment, the same three strategies should show no consistent speed-ordered selective advantage across seeds.**

The prediction is aggregate and environment-dependent. It does not require every individual replicate to follow the expected ordering, and disagreement in E4 is a scientific result to investigate rather than tune away.

## Claim boundaries

E3 supports these bounded conclusions:

- locomotor capacity has no detectable performance effect in the tested no-travel local-resource null;
- separated resource access creates a benefit to greater capacity at low-to-intermediate speeds;
- canonical quadratic locomotion expenditure creates a high-speed penalty;
- their combination produces an independently confirmed interior performance maximum near speed 3 in this controlled composition;
- removing locomotion cost removes the high-speed penalty and converts much of the landscape into a plateau.

E3 does **not** claim:

- that speed 3 is universally optimal;
- that the E3 landscape applies unchanged to B3 or the richer reference ecology;
- that monomorphic performance automatically determines mixed-population evolutionary dynamics;
- that simulation timesteps are biological generations;
- that organisms within a run are independent replicates;
- that a single scalar fitness variable is needed or meaningful.

E4 exists precisely to test whether standing inherited variation moves in the direction predicted independently by this monomorphic ecological-performance landscape.
