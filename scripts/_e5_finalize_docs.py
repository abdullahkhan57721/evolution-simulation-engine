from pathlib import Path

current = Path("docs/development/current_state.md")
text = current.read_text()

old_sequence = """E1–E4 now form a completed causal proof sequence above the frozen kernel and
separate from the richer reference ecology.

```text
E1 measurement semantics and reproducibility
        ↓
E2 minimal controlled locomotion mechanics
        ↓
E3 monomorphic ecological-performance landscape
        ↓
E4 selection on standing inherited variation
```
"""
new_sequence = """E1–E5 now form a completed causal proof sequence above the frozen kernel and
separate from the richer reference ecology.

```text
E1 measurement semantics and reproducibility
        ↓
E2 minimal controlled locomotion mechanics
        ↓
E3 monomorphic ecological-performance landscape
        ↓
E4 selection on standing inherited variation
        ↓
E5 finite-population drift and weak selection
```
"""
if old_sequence not in text:
    raise SystemExit("current-state E1-E4 sequence anchor not found")
text = text.replace(old_sequence, new_sequence, 1)

anchor = """E4 therefore supports E3's independently frozen prediction: under this controlled
finite-horizon ecology, the separated corridor selects for the intermediate
speed-3 strategy while the local-resource environment is frequency-neutral.
Mutation is off, so this is selection on standing variation rather than de novo
mutation-driven adaptation. The result is not a universal optimum or long-run
fixation claim. See `docs/e4_standing_variation.md`.
"""
e5 = anchor + """

### E5 — confirmed finite-population stochasticity and weak selection

E5 derives A/B ancestry only in the analysis layer from existing founder IDs and
`PedigreeRecorder`; neutral labels never enter modeled biology. Neutral runs use
identical speed-3 founders. Weak-selection runs compare speeds 3 and 4 with
founder-ID assignment counterbalanced and one run/seed as the replicate.

After one pre-confirmation resource correction exposed E2's existing randomized
scarce-resource allocation, the design was frozen. A single bounded 3-vs-2
diagnostic was rejected because it was substantially stronger than 3-vs-4.
Independent confirmation on 24 disjoint seeds shows neutral frequency-change SD
contracting across founder counts 2, 8, and 32 (`0.0319`, `0.0168`, `0.0102`).
The favored speed-3 strategy decreases in 2/24 weak-selection runs at two founders,
1/24 at eight founders, and 0/24 at 32 founders. Thus finite-run stochasticity can
obscure or reverse weak selection at small modeled population size.

No lineage loss, fixation, or whole-population extinction was observed within the
60-step confirmation horizon; those outcomes remain right-censored. The minimal
controlled composition has no ordinary aging/metabolic/density-independent
turnover, so E5 does not manufacture fixation. A later rare-lineage invasion must
use a matched neutral rare-lineage control with the same introduction state,
rarity, ecology, population context, and horizon rather than treating an unmatched
rare founder as the control. See `docs/e5_drift_weak_selection.md`.
"""
if anchor not in text:
    raise SystemExit("current-state E4 anchor not found")
text = text.replace(anchor, e5, 1)

old_front = """The planned E1→E4 controlled-science sequence is complete. It now provides a clean
causal chain from mechanics to ecological performance to environment-dependent
selection on inherited standing variation, alongside the richer independently
confirmed B3 flagship.

There is **no repository-defined E5 milestone** at this point. Do not invent one in
implementation chats. The next controlled-science or architecture milestone should
be chosen through roadmap reassessment and an explicit Issue if/when a concrete
scientific or architectural question earns it.
"""
new_front = """The E1→E5 controlled-science sequence is complete through the finite-population
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
if old_front not in text:
    raise SystemExit("current-state development-front anchor not found")
text = text.replace(old_front, new_front, 1)
text = text.replace(
    "The reference ecology, B3 flagship, and E2–E4 controlled experiments are",
    "The reference ecology, B3 flagship, and E2–E5 controlled experiments are",
)
text = text.replace(
    "The controlled E2–E4 program remains intentionally distinct",
    "The controlled E2–E5 program remains intentionally distinct",
)
recent_anchor = "Newest first; this is a capability summary, not a changelog.\n\n"
recent = """- **Confirmed drift and weak-selection baseline:** derived neutral ancestry only in
  the analysis layer from existing pedigree evidence, independently confirmed that
  neutral frequency-change spread contracts across founder counts 2/8/32, showed
  weak 3-vs-4 selection reversing in individual small-population runs, preserved
  unobserved loss/fixation/extinction as right-censored, and froze a matched-neutral
  rare-lineage control requirement for later invasion without adding mortality,
  fitness, or generic population-genetics machinery.
"""
if recent_anchor not in text:
    raise SystemExit("current-state recent-milestone anchor not found")
text = text.replace(recent_anchor, recent_anchor + recent, 1)
current.write_text(text)

roadmap = Path("docs/development/roadmap.md")
text = roadmap.read_text()
text = text.replace(
    "## Completed E1–E4 controlled-science sequence",
    "## Completed E1–E5 controlled-science sequence",
    1,
)
old_block = """E3 monomorphic ecological-performance landscape
        ↓
E4 selection on standing inherited variation
```
"""
new_block = """E3 monomorphic ecological-performance landscape
        ↓
E4 selection on standing inherited variation
        ↓
E5 finite-population drift and weak selection
```
"""
if old_block not in text:
    raise SystemExit("roadmap sequence block not found")
text = text.replace(old_block, new_block, 1)

e4_anchor = """Thus E4 fulfilled E3's independently frozen prediction for this controlled
finite-horizon ecology without adding a scalar fitness abstraction. It is selection
on standing variation, not a universal optimum, fixation claim, or de novo
mutation result.

E1–E4 are intentionally separate from B3. B3 remains the richer integrated
reference-ecology flagship; the E sequence isolates causal mechanics and does not
retroactively simplify B3.
"""
e5_section = """Thus E4 fulfilled E3's independently frozen prediction for this controlled
finite-horizon ecology without adding a scalar fitness abstraction. It is selection
on standing variation, not a universal optimum, fixation claim, or de novo
mutation result.

### E5 — drift, population size, and weak selection

E5 asks how reliable a weak selection signal remains under finite-population
stochasticity. It assigns neutral A/B ancestry only in analysis from founder IDs
and the existing clonal pedigree, so neutral lineages have identical modeled
biology. Founder counts 2, 8, and 32 are modeled regimes rather than real-world
effective population-size claims.

Independent confirmation shows neutral frequency-change spread contracting with
founder count while the small positive 3-vs-4 directional effect remains similar.
The favored speed-3 strategy reverses direction in some small-population runs but
not at the largest tested founder count. Loss/fixation/extinction remain outcomes
and are right-censored when absent; E5 does not introduce turnover merely to force
absorption.

The rare-invasion handoff is explicit: later invasion must compare disappearance
against a neutral lineage introduced in the same state and at the same rarity under
the same ecology, population context, and horizon. A rare founder is not
automatically a valid control for a de-novo mutant. Reuse E5's pedigree-derived
ancestry and run-level censoring rather than building a generic population-genetics
layer.

E1–E5 are intentionally separate from B3. B3 remains the richer integrated
reference-ecology flagship; the E sequence isolates causal mechanics and does not
retroactively simplify B3.
"""
if e4_anchor not in text:
    raise SystemExit("roadmap E4 anchor not found")
text = text.replace(e4_anchor, e5_section, 1)

old_next = """## Next milestone selection

There is currently **no repository-defined E5 milestone**. Do not infer one merely
because E1–E4 are complete. The next controlled-science or architecture milestone
should be chosen by roadmap reassessment around a concrete scientific question,
architectural pressure, or product need, then encoded in an explicit Issue.

Possible longer-term modeled fronts remain below, but they are directions rather
than preauthorized sequential milestones.
"""
new_next = """## Next controlled-science pressure

E5 establishes the finite-population baseline needed before rare-lineage invasion.
The next controlled-science milestone should test invasion only after its
introduction semantics are explicit enough to construct a matched neutral control.
That control must share the mutant treatment's introduction state, rarity,
population context, ecology, horizon, and evidence/censoring semantics.

Do not interpret disappearance as selection merely because a lineage is rare, and
do not add generic fixation/population-genetics architecture ahead of concrete
consumers. Longer-term modeled fronts remain directions rather than preauthorized
implementations.
"""
if old_next not in text:
    raise SystemExit("roadmap next-milestone anchor not found")
text = text.replace(old_next, new_next, 1)
text = text.replace(
    "E1–E4 provide concrete consumers for the scientific-measurement boundary",
    "E1–E5 provide concrete consumers for the scientific-measurement boundary",
)
roadmap.write_text(text)

mkdocs = Path("mkdocs.yml")
text = mkdocs.read_text()
nav_anchor = "  - E4 Standing Variation and Selection: e4_standing_variation.md\n"
if nav_anchor not in text:
    raise SystemExit("MkDocs E4 nav anchor not found")
text = text.replace(
    nav_anchor,
    nav_anchor + "  - E5 Drift, Population Size, and Weak Selection: e5_drift_weak_selection.md\n",
    1,
)
mkdocs.write_text(text)
