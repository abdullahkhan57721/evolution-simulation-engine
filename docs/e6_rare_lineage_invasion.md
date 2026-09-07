# E6 — Rare-Lineage Invasion and Candidate Stability

E6 asks a narrower question than E4 or E5:

> After a resident population has already begun establishing in the controlled
> corridor, can a rare alternative locomotor strategy increase its realized
> reproductive contribution relative to an otherwise identical rare entrant?

The experiment remains above the frozen kernel and reuses the E1–E5 controlled
science contracts. It does not introduce a scalar fitness value, a generic
population-genetics layer, a generic intervention language, or a formal
Evolutionarily Stable Strategy (ESS) solver.

## Scientific position in the controlled sequence

```text
E1 measurement / replicate semantics
        ↓
E2 controlled locomotion mechanics
        ↓
E3 monomorphic performance landscape
        ↓
E4 selection on standing variation
        ↓
E5 drift + matched-neutral rare-lineage requirement
        ↓
E6 established-resident rare-lineage invasion
```

E3 independently identified `max_speed = 3` as the corridor's monomorphic
performance maximum. E4 then showed selection toward speed 3 when speeds 1, 3, and
9 coexist as standing inherited variation. E5 showed why a rare lineage cannot be
interpreted without a neutral baseline: finite-population stochasticity and
introduction context can change lineage frequencies even when modeled biology is
identical.

E6 therefore tests reciprocal invasion between the nearby speeds 3 and 4 while
giving every mutant arm an exact matched neutral rare-entry control.

## Frozen experimental design

The final E6 assay is deliberately concrete.

### Resident ecology

Each resident population begins with:

- 8 monomorphic resident founders;
- either resident `max_speed = 4` or resident `max_speed = 3`;
- the E3 axis-aligned separated-resource corridor;
- 420 initial resource units per resident founder, or 3360 total;
- the same four E3 corridor deposit locations with the resource total split equally;
- canonical quadratic locomotion-use cost;
- E2 clonal inheritance;
- mutation disabled;
- all other nonfocal E2 biology unchanged.

The resident-only simulation runs for **10 committed steps** before intervention.
The final observation horizon remains committed step **60**, giving **50
post-introduction committed steps**.

At step 10 the discovery and confirmation checkpoints still contain all 8 resident
organisms, so one admitted rare organism starts at frequency `1/9 ≈ 0.1111`. This
is a controlled low-frequency assay, not an asymptotic infinitesimal-frequency
invasion analysis.

### Reciprocal invasion treatments

Two resident backgrounds are tested:

1. resident speed 4 with a rare speed-3 mutant;
2. resident speed 3 with a rare speed-4 mutant.

Each is paired with a neutral external entrant whose speed equals the resident:

- resident 4 + rare speed-4 neutral entrant;
- resident 4 + rare speed-3 mutant entrant;
- resident 3 + rare speed-3 neutral entrant;
- resident 3 + rare speed-4 mutant entrant.

For one seed and resident background, neutral and mutant arms fork from the **same
exact burn-in state**.

## Exact matched-state fork

E6 uses the existing in-memory `SimulationState.copy()` contract rather than adding
checkpoint serialization or a new kernel API.

```text
resident-only simulation
        ↓
committed step-10 state
        ↓
exact SimulationState.copy()
        ↓
        ├── neutral external admission
        └── mutant external admission
        ↓
post-introduction simulation to step 60
```

The copied checkpoint preserves the mutable world, simulation step, allocator
state, immutable context, and RNG state. E6 records deterministic SHA-256
fingerprints for the resident world and RNG state in experiment provenance so that
matched arms can be audited as sharing the same pre-intervention history.

The two arms then use the same organism-ID allocator state, the same resident
population, the same resource field, the same RNG state, and the same deterministic
introduction location. The only modeled difference is the admitted organism's
`max_speed`.

## External-admission semantics

The rare entrant is **not** represented as a natural `Reproduction.Event` and is
not represented as a simulated mutation.

It is an explicit experiment-layer intervention:

`experiment_external_newborn_like_admission`

The admitted organism has:

- age `0`;
- energy `20`, matching E2 newborn reproductive investment;
- body mass `1`;
- mating type `clonal`;
- a haploid one-locus genome with the arm's declared `max_speed`;
- the current position of the lowest-ID living resident at the burn-in checkpoint.

The deterministic resident anchor avoids consuming RNG and gives neutral and mutant
entrants the same position. It also approximates E2's natural source-location
newborn semantics more closely than placing an external newborn back at the
historical founder coordinate.

Because admission is external, no parent is assigned and no resident pays the
20-unit reproductive energy transfer. That extra organism and energy are therefore
an experimental perturbation. The **matched neutral arm receives exactly the same
perturbation**, which is why mutant interpretation is comparative rather than based
on the mutant arm alone.

## Analysis-only lineage identity

Fresh post-introduction `IndividualGeneticTraitRecorder` and `PedigreeRecorder`
instances begin at committed step 10.

At that baseline:

- the admitted organism is labeled `rare` only in E6 analysis;
- every other baseline organism is labeled `resident` only in E6 analysis;
- subsequent single-parent clonal descendants inherit the resolved analysis label
  through the committed pedigree.

No resident/rare lineage label enters `Organism`, the genome, the simulation
configuration, movement, feeding, reproduction, or conflict resolution. E6 also
checks that committed `max_speed` remains consistent with resolved ancestry.

## Outcomes and replicate unit

One seed-level resident history is one stochastic replicate. The neutral and mutant
arms are a matched pair derived from that same history. Organisms within a run are
not independent replicates.

For every post-introduction committed state E6 preserves:

- complete resident and rare counts;
- resident and rare frequencies, undefined after whole-population extinction;
- final-minus-initial rare frequency change;
- final-minus-initial rare count change;
- first rare expansion from count 1 to count at least 2;
- first rare-lineage loss while residents remain;
- fixation winner/time if observed;
- whole-population extinction if observed;
- rare-lineage realized births/descendants from pedigree evidence.

Loss, fixation, and extinction use the E1 `FixedHorizonTimeToEvent` contract and are
right-censored when unobserved.

The primary selective comparison is paired within seed and resident background:

```text
mutant rare-frequency change
-
matched-neutral rare-frequency change
```

E6 reports the replicate-level paired contrasts and their mean/median and
positive/negative/unchanged proportions. These are experiment-specific descriptive
summaries, not a generic fitness coefficient.

## Protocol validation before freeze

E6 preserved the distinction between technical assay validation and scientific
confirmation.

### Early confirmation candidates were retired

The initial draft workflow accidentally executed an originally proposed confirmation
seed set before the experimental design was frozen. Those seeds were immediately
disqualified from independent confirmation and are not used in the E6 result.

### Historical founder-coordinate admission was invalid

The first implementation placed the 20-energy newborn-like entrant at the old E3
founder coordinate `(10, 15)`. The first corridor resource is 12 cells away, so in
the canonical quadratic-cost system a speed-3 or speed-4 newborn cannot
energetically reach it. That implementation smoke test measured a bad introduction
location rather than invasion. Before legitimate discovery, placement was corrected
to the deterministic living-resident anchor described above.

### Twenty-step burn-in remained degenerate

The six declared discovery seeds were then run with the candidate 20-step burn-in.
By step 20 the resident populations had already expanded to roughly 17–23
organisms. Every rare entrant remained at count 1 and produced zero descendants,
even though substantial resources remained.

The Issue had predeclared at most one bounded timing adjustment if the candidate
assay was technically degenerate. E6 used that allowance to move admission from
step 20 to step 10 while retaining terminal step 60. No focal biology, strategy
pair, resource scale, entrant state, matched-control semantics, or outcome was
changed after that adjustment.

## Discovery after the bounded timing adjustment

The frozen-design discovery seeds are:

`(13, 31, 47, 73, 101, 127)`

### Speed 3 invading resident speed 4

Across six matched pairs:

- neutral speed-4 entrants expanded in `0/6` runs and produced no descendants;
- speed-3 mutants expanded in `4/6` runs and averaged `0.667` rare births;
- mean mutant-minus-neutral rare-frequency contrast was `+0.0116`;
- `5/6` paired contrasts were positive and `1/6` was negative.

### Speed 4 invading resident speed 3

Across six matched pairs:

- neither neutral speed-3 nor mutant speed-4 entrants expanded;
- neither produced descendants;
- mean mutant-minus-neutral rare-frequency contrast was approximately `-0.0005`.

The assay was therefore scientifically usable and the 10+50 design was frozen
without further tuning.

## Independent confirmation

Confirmation used 24 fresh seeds that were disjoint from discovery and from the
prematurely exposed candidate set:

`(509, 521, 523, 541, 547, 557, 563, 569, 571, 577, 587, 593, 599, 601, 607, 613, 617, 619, 631, 641, 643, 647, 653, 659)`

No replicate was filtered.

### Resident speed 4; rare speed-3 mutant

Matched neutral speed-4 entrants:

- rare expansion: `0/24`;
- mean rare births: `0`;
- mean final-minus-initial rare-frequency change: approximately `-0.0919`.

Rare speed-3 mutants:

- rare expansion / at least one rare descendant: `8/24`;
- mean rare births: `0.333`;
- mean rare-frequency change: approximately `-0.0865`.

Paired mutant-minus-neutral frequency contrast:

- mean: approximately **`+0.0055`**;
- positive: `13/24`;
- negative: `9/24`;
- unchanged: `2/24`.

### Resident speed 3; rare speed-4 mutant

Matched neutral speed-3 entrants and mutant speed-4 entrants both showed:

- rare expansion: `0/24`;
- mean rare births: `0`.

Paired mutant-minus-neutral frequency contrast:

- mean: approximately **`-0.0001`**;
- positive: `8/24`;
- negative: `10/24`;
- unchanged: `6/24`.

The small nonzero endpoint contrasts here arise from differences in the surrounding
resident population trajectories after the two arms diverge; they are not rare
speed-4 reproduction.

No rare-lineage loss, fixation, or whole-population extinction was observed in the
fixed confirmation horizon. Those event times remain right-censored rather than
being treated as zero-duration or absent outcomes.

## Interpretation

E6 independently confirms a **directional reciprocal asymmetry** in this controlled
corridor assay:

- a rare speed-3 lineage can achieve reproductive expansion in an established
  speed-4 resident population and outperforms its exact matched neutral rare-entry
  baseline on average;
- a rare speed-4 lineage does not achieve reproductive expansion against established
  speed-3 residents and does not show a positive average matched invasion contrast.

Together with E3 and E4, this supports describing speed 3 as a **candidate
invasion-stable strategy against reciprocal speed 4 in this particular controlled
assay**.

That wording is intentionally narrower than an ESS claim. E6 does **not** establish:

- a formal ESS across all nearby or distant strategies;
- asymptotic invasion fitness;
- long-run fixation or loss;
- a universal optimal speed;
- general ecological stability outside the tested E2/E3 corridor;
- an equilibrium population-genetics model;
- a species-calibrated biological prediction.

A further important nuance is that every confirmation arm finishes with rare
frequency below its initial `1/9`. The resident population grows substantially
after admission. Raw endpoint frequency decline therefore cannot by itself diagnose
selection against the entrant. The predeclared evidence is the **matched
mutant-minus-neutral contrast plus realized rare-lineage reproduction/expansion**.

## Architectural outcome and handoff

E6 demonstrates that established-population interventions can be tested rigorously
without changing the kernel or inventing generic intervention/population-genetics
infrastructure. The reusable lessons are narrower contracts:

- exact in-memory state/RNG forking is sufficient for matched post-history arms;
- intervention provenance must be explicit when the intervention is not a simulated
  biological event;
- pedigree can support analysis-only ancestry after an intervention baseline;
- rare-lineage interpretation needs a matched neutral introduction baseline;
- run-level pairing and right-censoring remain first-class scientific semantics.

## E7 handoff — Mutation-Driven Adaptation and Convergence

E7 should begin only after E6 is merged and verified. It changes the scientific
question from invasion of supplied rare strategies to adaptation when the focal
`max_speed` locus itself can mutate.

The planned E7 design pressure is deliberately bounded:

- mutate only the focal locomotor locus; do not enable mutation across the richer
  reference genome;
- use multiple predeclared starting populations spanning low speed, the E3–E6
  predicted region, and high speed;
- use multiple independent seeds for each starting condition;
- define a legal speed range wider than the expected adaptive region;
- make mutation rate and mutation-step distribution explicit;
- preserve full committed `max_speed` distributions rather than reporting only a
  population mean;
- distinguish convergence, stationary variation, persistent polymorphism,
  directional evolution, boundary accumulation, and extinction;
- treat accumulation at a configured speed boundary as a diagnostic, not as proof
  of an optimum.

The scientific comparison should connect E7 back to the existing causal chain:
E3's monomorphic performance region, E4's standing-variation selection direction,
and E6's bounded reciprocal invasion result. E7 should not add a universal fitness,
adaptive-landscape, mutation, or population-genetics framework merely because the
focal mutation experiment now needs one concrete mutation policy.
