from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


current_path = Path("docs/development/current_state.md")
current = current_path.read_text()

current = replace_once(
    current,
    "E1–E5 now form a completed causal proof sequence above the frozen kernel and\n"
    "separate from the richer reference ecology.",
    "E1–E6 now form a completed causal proof sequence above the frozen kernel and\n"
    "separate from the richer reference ecology.",
    "current-state sequence heading",
)
current = replace_once(
    current,
    "E5 finite-population drift and weak selection\n```",
    "E5 finite-population drift and weak selection\n"
    "        ↓\n"
    "E6 rare-lineage invasion and candidate stability\n```",
    "current-state sequence diagram",
)

old_e5_tail = """turnover, so E5 does not manufacture fixation. A later rare-lineage invasion must
use a matched neutral rare-lineage control with the same introduction state,
rarity, ecology, population context, and horizon rather than treating an unmatched
rare founder as the control. See `docs/e5_drift_weak_selection.md`.

## Experiment Workbench authoring foundation
"""
new_e5_e6 = """turnover, so E5 does not manufacture fixation. E6 directly consumed that
requirement by using a matched neutral rare-lineage control with the same
introduction state, rarity, ecology, population context, and horizon rather than
treating an unmatched rare founder as the control. See
`docs/e5_drift_weak_selection.md`.

### E6 — confirmed rare-lineage invasion and candidate stability

E6 runs a genuine resident-only burn-in and then forks the exact committed
`SimulationState`, including RNG and allocator state, into matched neutral and
mutant arms. The external entrant is explicit experiment provenance rather than a
simulated birth or mutation. It is newborn-like (age 0, energy 20, body mass 1), is
placed at the current position of the lowest-ID living resident without consuming
RNG, and differs across paired arms only in `max_speed`. Resident/rare identity
remains analysis-only and propagates through existing pedigree evidence.

The frozen assay uses eight monomorphic residents, the E3 separated-resource
corridor at E5's corrected resource scale, a 10-step resident burn-in, and terminal
step 60. It tests reciprocal speed 3↔4 invasion, with each mutant arm compared to an
exact matched neutral rare entrant from the same resident history.

Independent confirmation on 24 fresh seeds shows speed-3 mutants expanding in
`8/24` speed-4 resident runs versus `0/24` matched neutral controls, with mean
paired rare-frequency contrast approximately `+0.0055`. Reciprocal speed-4 mutants
expand in `0/24` runs and have an essentially zero/slightly negative mean paired
contrast (`-0.0001`). No rare-lineage loss, fixation, or whole-population extinction
is observed within the fixed horizon, so those event times remain right-censored.

The result supports speed 3 only as a **candidate invasion-stable strategy against
reciprocal speed 4 in this controlled corridor assay**. It is not a formal ESS,
fixation result, asymptotic invasion-fitness estimate, or universal optimal-speed
claim. See `docs/e6_rare_lineage_invasion.md`.

## Experiment Workbench authoring foundation
"""
current = replace_once(
    current,
    old_e5_tail,
    new_e5_e6,
    "current-state E5/E6 handoff",
)
current = replace_once(
    current,
    "reinterpreted by E2–E5 or the Workbench.",
    "reinterpreted by E2–E6 or the Workbench.",
    "current-state B3 scope",
)

old_front = """The E1→E5 controlled-science sequence is complete through the finite-population
baseline. It provides a causal chain from mechanics to ecological performance,
selection on inherited standing variation, and the stochastic reliability of weak
selection across modeled founder-count regimes, alongside the richer independently
confirmed B3 flagship.

The next controlled-science pressure is rare-lineage invasion. Any such milestone
must preserve E5's key interpretation boundary: disappearance of a rare lineage is
not by itself evidence of selective disadvantage. If the invasion design can lose
a rare lineage, it must include a matched neutral control using the same
introduction mechanism/state, initial rarity, population context, ecology, horizon,
and censoring semantics. Do not retrofit mortality or generic population-genetics
machinery merely to obtain textbook fixation behavior.
"""
new_front = """The E1→E6 controlled-science sequence is complete through the first matched
established-resident rare-lineage invasion assay. It now provides a causal chain
from locomotion mechanics through ecological performance, standing-variation
selection, finite-population stochasticity, and reciprocal invasion evidence,
alongside the richer independently confirmed B3 flagship.

The next planned controlled-science milestone is **E7 — Mutation-Driven Adaptation
and Convergence**. E7 should ask whether independent populations with focal-only
`max_speed` mutation converge toward the performance/selection/invasion region
identified by E3–E6. It should use multiple predeclared low/near/high starting
conditions, an explicit mutation rate and step distribution, a legal speed range
wider than the expected adaptive region, and full trait-distribution evidence.
Boundary accumulation, polymorphism, stationary variation, directional evolution,
and extinction must remain distinguishable; boundary pile-up or a population mean
must not be promoted to an optimum. Mutation must remain isolated to the focal
locomotor locus rather than being enabled across the richer reference genome.
"""
current = replace_once(
    current,
    old_front,
    new_front,
    "current-state development front",
)
current = current.replace(
    "the reference ecology, B3 flagship, and E2–E5 controlled experiments",
    "the reference ecology, B3 flagship, and E2–E6 controlled experiments",
)
current = current.replace(
    "The controlled E2–E5 program remains intentionally distinct",
    "The controlled E2–E6 program remains intentionally distinct",
)

milestone_anchor = "- **WB4 bounded reference-ecology custom study:**"
e6_milestone = """- **Confirmed rare-lineage invasion and candidate stability:** established exact
  resident-state/RNG forking, explicit matched external newborn-like admission,
  analysis-only pedigree ancestry, reciprocal speed-3/speed-4 invasion, and
  independent confirmation that speed 3 can reproduce and expand against speed-4
  residents while reciprocal speed 4 does not expand. The claim remains bounded
  to candidate stability against speed 4 without a formal ESS, fixation, scalar
  fitness, or generic intervention/population-genetics framework.
"""
current = replace_once(
    current,
    milestone_anchor,
    e6_milestone + milestone_anchor,
    "current-state recent milestone",
)
current_path.write_text(current)

roadmap_path = Path("docs/development/roadmap.md")
roadmap = roadmap_path.read_text()
roadmap = replace_once(
    roadmap,
    "## Completed E1–E5 controlled-science sequence",
    "## Completed E1–E6 controlled-science sequence",
    "roadmap sequence heading",
)
roadmap = replace_once(
    roadmap,
    "E5 finite-population drift and weak selection\n```",
    "E5 finite-population drift and weak selection\n"
    "        ↓\n"
    "E6 rare-lineage invasion and candidate stability\n```",
    "roadmap sequence diagram",
)

old_handoff = """The rare-invasion handoff is explicit: later invasion must compare disappearance
against a neutral lineage introduced in the same state and at the same rarity under
the same ecology, population context, and horizon. A rare founder is not
automatically a valid control for a de-novo mutant. Reuse E5's pedigree-derived
ancestry and run-level censoring rather than building a generic population-genetics
layer.

E1–E5 are intentionally separate from B3. B3 remains the richer integrated
reference-ecology flagship; the E sequence isolates causal mechanics and does not
retroactively simplify B3.
"""
new_handoff = """The rare-invasion handoff required later invasion to compare disappearance against a
neutral lineage introduced in the same state and at the same rarity under the same
ecology, population context, and horizon. E6 directly consumes that requirement.

### E6 — rare-lineage invasion and candidate stability

E6 uses eight monomorphic residents through a genuine 10-step burn-in in the E3
corridor, then forks the exact committed state/RNG into matched external-admission
arms. The newborn-like entrant is placed at a deterministic living resident's
current position and differs between paired arms only in `max_speed`; resident/rare
ancestry remains analysis-only through existing pedigree evidence. Reciprocal speed
3↔4 invasion is followed to terminal step 60.

Independent confirmation on 24 fresh seeds shows speed-3 mutants producing rare
descendants and expanding in `8/24` speed-4 resident runs versus `0/24` matched
neutral controls, with positive mean paired frequency contrast (`+0.0055`).
Reciprocal speed-4 mutants expand in `0/24` runs and have an essentially zero to
slightly negative average invasion signal. Loss, fixation, and extinction remain
right-censored because E6 does not retrofit turnover merely to force absorption.

This is a bounded **candidate invasion-stability** result against reciprocal speed
4, not a formal ESS, asymptotic invasion-fitness estimate, fixation result, or
universal optimum. E6 establishes no generic intervention or population-genetics
framework; future generalization requires another concrete scientific consumer.

E1–E6 are intentionally separate from B3. B3 remains the richer integrated
reference-ecology flagship; the E sequence isolates causal mechanics and does not
retroactively simplify B3.
"""
roadmap = replace_once(
    roadmap,
    old_handoff,
    new_handoff,
    "roadmap E5/E6 handoff",
)

old_next = """## Next controlled-science pressure

E5 establishes the finite-population baseline needed before rare-lineage invasion.
The next controlled-science milestone should test invasion only after its
introduction semantics are explicit enough to construct a matched neutral control.
That control must share the mutant treatment's introduction state, rarity,
population context, ecology, horizon, and evidence/censoring semantics.

Do not interpret disappearance as selection merely because a lineage is rare, and
do not add generic fixation/population-genetics architecture ahead of concrete
consumers. Longer-term modeled fronts remain directions rather than preauthorized
implementations.

The Workbench product track proceeds independently from this scientific sequence.
A scientific milestone should not acquire Workbench dependencies merely because
the Workbench exists, and Workbench expansion should continue to compile into
already settled simulation/science contracts.
"""
new_next = """## Next controlled-science pressure

### E7 — mutation-driven adaptation and convergence

E7 is the next sequential controlled-science milestone after E6. Its central
question is:

> If evolution is no longer limited to supplied standing strategies, where does a
> population evolve when `max_speed` can mutate, and do independent populations
> converge toward the performance/selection/invasion region identified by E3–E6?

E7 should mutate **only the focal locomotor locus**. It must not enable mutation
across the richer reference genome merely for convenience. Use multiple
predeclared starting conditions spanning low speed, the predicted region, and high
speed, with multiple independent seeds. The legal speed domain should extend wider
than the expected adaptive region, and the mutation rate plus mutation-step
distribution must be explicit.

Preserve full committed trait distributions rather than relying on population
means. Distinguish genuine convergence from stationary variation, persistent
polymorphism, directional evolution, boundary accumulation, and extinction. A
pile-up at a configured trait boundary is not evidence of an optimum. Compare E7's
outcomes against the causal chain already established by E3's performance region,
E4's selection direction, and E6's bounded invasion-stability region.

E7 should remain above the frozen kernel and should not introduce a universal
adaptive-landscape, fitness, mutation, or population-genetics framework unless a
concrete deficiency in existing contracts is independently demonstrated.

The Workbench product track remains orthogonal to this scientific sequence. E7
should not acquire Workbench dependencies merely because the Workbench exists.
"""
roadmap = replace_once(
    roadmap,
    old_next,
    new_next,
    "roadmap next controlled science",
)
roadmap_path.write_text(roadmap)
