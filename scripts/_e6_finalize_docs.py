"""Temporarily finalize E6 orientation against current main."""

from __future__ import annotations

import subprocess
from pathlib import Path


def _git_show(path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"origin/main:{path}"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def _replace_once(text: str, old: str, new: str, *, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


def _replace_between(
    text: str,
    start: str,
    end: str,
    replacement: str,
    *,
    label: str,
) -> str:
    start_index = text.find(start)
    if start_index < 0:
        raise RuntimeError(f"{label}: start marker not found")
    end_index = text.find(end, start_index + len(start))
    if end_index < 0:
        raise RuntimeError(f"{label}: end marker not found")
    return text[:start_index] + replacement + text[end_index:]


def _patch_current_state() -> None:
    path = Path("docs/development/current_state.md")
    text = _git_show(path.as_posix())
    text = _replace_once(
        text,
        "E1–E5 now form a completed causal proof sequence above the frozen kernel and\nseparate from the richer reference ecology.",
        "E1–E6 now form a completed causal proof sequence above the frozen kernel and\nseparate from the richer reference ecology.",
        label="current sequence summary",
    )
    text = _replace_once(
        text,
        """E4 selection on standing inherited variation
        ↓
E5 finite-population drift and weak selection
```""",
        """E4 selection on standing inherited variation
        ↓
E5 finite-population drift and weak selection
        ↓
E6 rare-lineage invasion and candidate stability
```""",
        label="current sequence diagram",
    )
    text = _replace_once(
        text,
        """A later rare-lineage invasion must
use a matched neutral rare-lineage control with the same introduction state,
rarity, ecology, population context, and horizon rather than treating an unmatched
rare founder as the control.""",
        """E6 directly consumed that requirement by using a matched neutral rare-lineage
control with the same introduction state, rarity, ecology, population context, and
horizon rather than treating an unmatched rare founder as the control.""",
        label="E5 handoff consumption",
    )
    e6_section = """
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

"""
    text = _replace_once(
        text,
        "\n## Experiment Workbench authoring foundation\n",
        e6_section + "## Experiment Workbench authoring foundation\n",
        label="current E6 section insertion",
    )
    current_front = """## Current development front

The E1→E6 controlled-science sequence is complete through the first matched
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
    text = _replace_between(
        text,
        "## Current development front\n\n",
        "The Workbench product front now",
        current_front,
        label="current development front",
    )
    text = _replace_once(
        text,
        """Newest first; this is a capability summary, not a changelog.

- **WB3 controlled experiment authoring:**""",
        """Newest first; this is a capability summary, not a changelog.

- **Confirmed rare-lineage invasion and candidate stability:** established exact
  resident-state/RNG forking, explicit matched external newborn-like admission,
  analysis-only pedigree ancestry, reciprocal speed-3/speed-4 invasion, and
  independent confirmation that speed 3 can reproduce and expand against speed-4
  residents while reciprocal speed 4 does not expand. The claim remains bounded
  to candidate stability against speed 4 without a formal ESS, fixation, scalar
  fitness, or generic intervention/population-genetics framework.
- **WB3 controlled experiment authoring:**""",
        label="recent E6 milestone",
    )
    text = text.replace("E2–E5 controlled experiments", "E2–E6 controlled experiments")
    text = text.replace(
        "reinterpreted by E2–E5 or the Workbench",
        "reinterpreted by E2–E6 or the Workbench",
    )
    text = text.replace("E1–E5 controlled-science", "E1–E6 controlled-science")
    path.write_text(text, encoding="utf-8")


def _patch_roadmap() -> None:
    path = Path("docs/development/roadmap.md")
    text = _git_show(path.as_posix())
    e6_section = """
### E6 — rare-lineage invasion and candidate stability

E6 consumes E5's matched-neutral requirement directly. Eight monomorphic residents
run through a genuine 10-step burn-in in the E3 corridor; the exact committed
state/RNG is then forked into matched external-admission arms. The newborn-like
entrant is placed at a deterministic living resident's current position and differs
between paired arms only in `max_speed`; resident/rare ancestry remains analysis-
only through existing pedigree evidence. Reciprocal speed 3↔4 invasion is followed
to terminal step 60.

Independent confirmation on 24 fresh seeds shows speed-3 mutants producing rare
descendants in `8/24` speed-4 resident runs versus `0/24` matched neutral controls,
with positive mean paired frequency contrast (`+0.0055`). Reciprocal speed-4 mutants
produce no descendants in `24/24` runs and have no positive average invasion
signal. Loss, fixation, and extinction remain right-censored because E6 does not
retrofit turnover merely to force absorption.

This is a bounded **candidate invasion-stability** result against reciprocal speed
4, not a formal ESS, asymptotic invasion-fitness estimate, fixation result, or
universal optimum. E6 establishes no generic intervention or population-genetics
framework; future generalization requires another concrete scientific consumer.

"""
    text = _replace_once(
        text,
        "E1–E5 are intentionally separate from B3.",
        e6_section + "E1–E6 are intentionally separate from B3.",
        label="roadmap E6 insertion",
    )
    e7_section = """## Next controlled-science pressure

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

"""
    text = _replace_between(
        text,
        "## Next controlled-science pressure\n\n",
        "## Front A — Richer genetic expression",
        e7_section,
        label="roadmap E7 handoff",
    )
    text = text.replace("E1–E5 are intentionally", "E1–E6 are intentionally")
    text = text.replace("E2–E5", "E2–E6")
    path.write_text(text, encoding="utf-8")


def _patch_e6_doc() -> None:
    path = Path("docs/e6_rare_lineage_invasion.md")
    text = path.read_text(encoding="utf-8")
    if "## E7 handoff — Mutation-Driven Adaptation and Convergence" in text:
        return
    marker = (
        "Future controlled-science work should build from the concrete question it wants to\n"
        "answer rather than generalizing E6 into a universal invasion framework."
    )
    marker_index = text.find(marker)
    if marker_index < 0:
        raise RuntimeError("E6 document handoff marker not found")
    text = text[:marker_index] + """## E7 handoff — Mutation-Driven Adaptation and Convergence

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
"""
    path.write_text(text, encoding="utf-8")


def _patch_mkdocs() -> None:
    path = Path("mkdocs.yml")
    text = _git_show(path.as_posix())
    text = _replace_once(
        text,
        """  - E5 Drift, Population Size, and Weak Selection: e5_drift_weak_selection.md
  - Exact Checkpoint and Resume: checkpointing.md
""",
        """  - E5 Drift, Population Size, and Weak Selection: e5_drift_weak_selection.md
  - E6 Rare-Lineage Invasion and Candidate Stability: e6_rare_lineage_invasion.md
  - Exact Checkpoint and Resume: checkpointing.md
""",
        label="MkDocs E6 navigation",
    )
    path.write_text(text, encoding="utf-8")


def main() -> None:
    _patch_current_state()
    _patch_roadmap()
    _patch_e6_doc()
    _patch_mkdocs()


if __name__ == "__main__":
    main()
