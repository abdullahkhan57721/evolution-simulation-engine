# WB4 — Bounded Reference-Ecology Workbench Recipe

WB4 adds the first rich custom biological study recipe to the Evolution Experiment
Workbench. It proves that the Workbench can author an integrated reference ecology
without mirroring `ReferenceEcologyConfig`, serializing policy objects, or creating
a second simulation architecture.

The dependency direction remains:

```text
Workbench semantic authoring
        ↓
bounded-reference-ecology recipe
        ↓
immutable resolved scientific manifest
        ↓
ReferenceEcologyConfig + build_reference_spec()
        ↓
BiologicalSimulationSpec.compile()
        ↓
SimulationSpec.compile()
        ↓
frozen kernel
```

Lower engine/domain packages remain independent of `evo_engine.workbench`.

## Recipe identity

The persisted scientific/compiler identity is:

```text
recipe ID       = bounded-reference-ecology
recipe version  = 1
compiler ID     = workbench.bounded-reference-ecology
compiler version= 1
```

Stable recipe-scoped semantic IDs such as
`reference-ecology.founder-max-speed` and
`reference-ecology.resource-geography` are the durable authoring identity. Python
module paths, class names, `ReferenceEcologyConfig` field paths, and object graphs
are not persisted scientific identity.

## Support tiers

WB4 makes support classification explicit while keeping it recipe-local.

### Guided

The initial Guided surface contains:

- world width and height (`4..50` each);
- founder population (`2..100`);
- founder starting energy (`1..200`);
- run horizon (`1..500`) and integer reproducibility seed;
- founder `max_speed` (`0..4`);
- founder `sensory_range` (`0..20`);
- founder `sensory_accuracy` (`0..100`);
- exploration movement: Moore, von Neumann, uniform, or Gaussian;
- resource geography: uniform or the bounded explicit two-patch form.

These are Workbench support limits, not new biological invariants. Existing lower
reference/configuration validation remains authoritative for cross-field and
modeled constraints.

### Advanced

The initial Advanced surface contains:

- Gaussian standard deviation (`0..10`), only for Gaussian exploration;
- renewable resource amount (`1..100`);
- resource deposits per step (`1..50`);
- two explicit patch centers and radii, only for two-patch geography;
- mutation enabled/disabled;
- mutation probability (`0..100000` ppm) and mutation max change (`1..4`), only
  while mutation is enabled;
- recombination probability (`0..1000000` ppm).

Patch centers are additionally constrained to the authored world bounds before the
existing lower reference preflight is invoked.

### Expert

WB4 deliberately exposes no Expert slots. The tier exists as an operational
classification, but no control was manufactured merely to populate it.

### Extension/internal

The following existing capabilities remain outside the official WB4 authoring
surface:

- arbitrary resource-placement policies, patch counts, or weights;
- arbitrary reference traits and physiological tradeoff editing;
- arbitrary loci, chromosomes, ploidy, or expression policies;
- inheritance-policy switching;
- generic reproduction-system composition;
- food-targeted or mate-targeted movement policy graphs;
- lifecycle/process swapping;
- arbitrary development/G×E policy editing.

Those exclusions are intentional product/recipe boundaries, not claims that the
engine lacks the underlying capability.

## Applicability and stale-state normalization

Applicability is explicit and local to this recipe; WB4 does not introduce a
universal dependency/capability solver.

Three transitions are normalized before scientific persistence:

```text
non-Gaussian exploration
    → gaussian_standard_deviation absent

mutation disabled
    → mutation_probability_ppm absent
    → mutation_max_change absent
    → effective mutation probability/change derived as zero

uniform resource geography
    → all two-patch geometry absent
```

Saved `ReferenceStudyRevision` values persist the normalized intent as well as the
resolved manifest. Inactive values therefore cannot survive invisibly in saved
editable state and reappear when a later fork re-enables a control.

Loading a saved revision also rechecks that normalized intent is still inside the
v1 Workbench support envelope and exactly matches the stored manifest. This catches
a persisted study whose intent and manifest were jointly altered to bypass the
supported authoring range.

## Explicit versus derived scientific meaning

`ReferenceEcologyIntent` stores only editable semantic choices.
`ReferenceEcologyManifest` stores a canonical immutable resolved value containing:

- recipe/compiler/software compatibility identity;
- normalized active explicit semantic slots;
- recipe-derived resource-placement and movement meaning;
- effective mutation meaning;
- fixed genetics/expression/inheritance/development/reproduction/targeting meaning;
- a canonical compatibility fingerprint of every non-editable numeric
  `ReferenceEcologyConfig` assumption that can change the modeled science.

The fixed-config fingerprint includes the non-exposed founder traits,
physiological tradeoffs, mating-type investment scales, energetics/growth scalars,
predation settings, resource-request/decomposition settings, mating radius, and
newborn-mass settings.

That fingerprint is important for exact reproduction: a future change to a
non-editable reference default must fail compatibility rather than silently change
the behavior of an old saved WB4 study.

WB4 does not serialize `ReferenceEcologyConfig`, placement/movement policy objects,
`BiologicalSimulationSpec`, `SimulationSpec`, process graphs, recorders, or runtime
state.

## Compilation and validation

Resolution first applies the WB4 support envelope and normalization. Compilation
then reconstructs fresh existing objects through:

```text
ReferenceEcologyManifest
        ↓
ReferenceEcologyConfig
        ↓
build_reference_spec(...)
        ↓
BiologicalSimulationSpec.compile()
        ↓
SimulationSpec.compile()
```

Before compilation, persisted recipe/compiler/software identity and all derived
assumptions must match the compatible v1 implementation. The lower reference and
biological preflight remains authoritative for constraints that are not WB4 product
limits. For example, WB4 can consider a founder population value individually
supported while lower reference validation still rejects a population larger than
the authored world's cell count.

The durable user-facing persistence path is `ReferenceStudyRevision`: it accepts
only normalized, v1-supported intent whose explicit values exactly match the stored
manifest. `compile_reference_ecology()` remains the lower recipe compilation
primitive for an already-constructed compatible manifest; durable authoring/load
must not bypass the saved-revision contract.

## Evidence

Evidence intent is independent from simulation intent. WB4 can reconstruct fresh
existing concrete recorders for:

- population trait summaries;
- committed events;
- pedigree/life history;
- allele/genotype composition;
- spatial replay.

Recorder instances are created before `build_reference_spec(...).compile()` so the
ordinary dependency/preflight path remains authoritative. Runtime recorder state is
never persisted as configuration.

Spatial replay is opt-in and emits a non-blocking volume advisory because it stores
full committed world frames. WB4 does not add an evidence registry, dependency
solver, or generic metric/statistics framework.

## Save, run, fork, and diff

`ReferenceStudyRevision` persists:

- normalized semantic intent;
- the exact resolved manifest;
- evidence intent;
- revision/parent identity;
- completed-run provenance tied to the manifest digest.

`run_reference_study_revision()` executes the exact saved manifest and returns the
requested existing evidence together with Workbench run provenance and E1
`ScientificRunProvenance`. One run/seed remains the stochastic replicate.

Forking is immutable. Semantic diff compares stable recipe-owned scientific IDs and
separates explicit changes from recipe-derived consequences; it never diffs Python
objects or arbitrary config fields.

## What the rich recipe taught us about WB1

WB4 created real pressure in four places:

1. many more semantic slots require human-readable recipe-local metadata;
2. some controls are conditional and therefore require explicit applicability and
   stale-state normalization;
3. a richer simulation needs a broader curated evidence surface;
4. exact reproduction requires compatibility coverage for non-editable reference
   assumptions, not only the small editable surface.

No shared WB1 architectural contract needed to change. The pressure was additive:
WB4 could remain a sibling bounded recipe with its own intent, manifest, evidence
plan, persistence shape, metadata, and normalization while reusing the settled
principles of semantic identity, immutable resolved meaning, exact load,
compatibility pinning, fresh runtime reconstruction, lower preflight, immutable
forks, and semantic diff.

This is evidence against introducing a registry, universal Blueprint, reflection-
based form generator, capability graph, generic policy editor, universal persisted
study root, or alternate simulation architecture at this stage.

## Handoff to later Workbench milestones

Later result/presentation workflows may rely on WB4 to provide:

- a stable `bounded-reference-ecology` v1 recipe identity;
- explicit Guided/Advanced/Expert/Extension classification;
- normalized immutable explicit/derived manifest semantics;
- exact compatible saved-study reproduction;
- immutable fork lineage and recipe-scoped semantic diff;
- concrete population/event/pedigree/genetic/spatial evidence attached to exact
  Workbench and scientific run provenance.

They must not infer validation, claims, scalar fitness, generic metric meaning, or
renderer semantics from those values. Those remain separate scientific or
presentation responsibilities.
