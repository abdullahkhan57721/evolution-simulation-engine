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
    raise SystemExit("current-state sequence anchor not found")
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

E5 derives A/B ancestry only in analysis from existing founder IDs plus
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
rarity, population context, ecology, and horizon rather than treating an unmatched
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
must preserve E5's interpretation boundary: disappearance of a rare lineage is not
by itself evidence of selective disadvantage. If the invasion design can lose a
rare lineage, it must include a matched neutral control using the same introduction
mechanism/state, initial rarity, population context, ecology, horizon, and
censoring semantics. Do not retrofit mortality or generic population-genetics
machinery merely to obtain textbook fixation behavior.
"""
if old_front not in text:
    raise SystemExit("current-state development-front anchor not found")
text = text.replace(old_front, new_front, 1)
text = text.replace("E2–E4 controlled experiments", "E2–E5 controlled experiments")
text = text.replace("controlled E2–E4 program", "controlled E2–E5 program")
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
    raise SystemExit("current-state recent milestone anchor not found")
text = text.replace(recent_anchor, recent_anchor + recent, 1)
current.write_text(text)

roadmap = Path("docs/development/roadmap.md")
text = roadmap.read_text()
old_sequence = """The controlled experimental-evolution sequence is now:

```text
E1 experimental-science foundation
        |
        v
E2 minimal clonal locomotion system
   + mechanics validation
        |
        v
E3 ecological performance landscape
   with focal evolution disabled
        |
        v
E4 standing variation +
   environment-dependent selection
```
"""
new_sequence = """The controlled experimental-evolution sequence is now complete through E5:

```text
E1 experimental-science foundation
        |
        v
E2 minimal clonal locomotion system
   + mechanics validation
        |
        v
E3 ecological performance landscape
   with focal evolution disabled
        |
        v
E4 standing variation +
   environment-dependent selection
        |
        v
E5 finite-population drift +
   weak-selection reliability
```
"""
if old_sequence not in text:
    raise SystemExit("roadmap controlled-sequence anchor not found")
text = text.replace(old_sequence, new_sequence, 1)

old_e4 = """E4 should finally introduce known standing inherited speed variation with mutation
still off and ask whether strategy/focal-trait frequencies move in the direction
predicted independently by E3. Founder positions/labels must be counterbalanced,
and disagreement with E3 is a scientific result to investigate rather than tune
away.

This sequence is intentionally separate from B3. B3 remains the richer integrated
reference-ecology flagship; E2–E4 are controlled causal experiments that may reuse
general contracts without retroactively simplifying or rewriting B3.
"""
new_e5 = """E4 then introduced known standing inherited speed variation with mutation still off
and confirmed that strategy frequencies move in the direction predicted
independently by E3 under the separated corridor while the matched local-resource
arm remains neutral.

E5 now adds the finite-population reliability layer. Neutral A/B ancestry exists
only in analysis and is derived from founder IDs plus the existing clonal pedigree;
neutral lineages therefore have identical modeled biology. Across founder counts
2, 8, and 32, independent confirmation shows neutral frequency-change spread
contracting with population size while weak 3-vs-4 selection is reversed in some
small-population runs and becomes more reliable at the largest tested size.
Unobserved lineage loss, fixation, and extinction remain right-censored rather than
being forced by adding turnover.

The next controlled-science pressure is rare-lineage invasion. Its neutral control
must match the mutant lineage's introduction mechanism/state, initial rarity,
population context, ecology, horizon, and censoring semantics. An unmatched rare
founder is not automatically a valid control for a de-novo mutant. Reuse E5's
pedigree-derived ancestry and run-level loss/censoring measurements rather than
creating a generic population-genetics framework.

This sequence is intentionally separate from B3. B3 remains the richer integrated
reference-ecology flagship; E2–E5 are controlled causal experiments that may reuse
general contracts without retroactively simplifying or rewriting B3.
"""
if old_e4 not in text:
    raise SystemExit("roadmap E4 narrative anchor not found")
text = text.replace(old_e4, new_e5, 1)
text = text.replace(
    "while the E2–E4 controlled experiment\ntrack proceeds independently:",
    "while the E2–E5 controlled experiment\ntrack proceeds independently:",
    1,
)
old_stats = """E1 now defines the durable scientific-measurement semantics needed by the current
controlled experiment sequence while deliberately stopping short of a broad
statistics framework. Future repeated experimental patterns may justify additional
reusable statistical contracts, but only after concrete consumers establish what
actually repeats.
"""
new_stats = """E1–E5 now provide concrete consumers for the durable scientific-measurement
boundary while deliberately stopping short of a broad statistics framework. E5
adds run-level frequency distributions and probabilities without pooling organisms
or introducing a new statistics dependency. Future repeated experimental patterns
may justify additional reusable contracts only after concrete consumers establish
what actually repeats.
"""
if old_stats not in text:
    raise SystemExit("roadmap statistics anchor not found")
text = text.replace(old_stats, new_stats, 1)
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
