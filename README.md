# Evolution Simulation Engine

Evolution Simulation Engine is a Python 3.12 simulation and scientific-workbench
project for studying heritable change in evolving populations without making
biological assumptions part of the execution kernel. A frozen domain-neutral
transactional kernel sits below general-evolution contracts, compositional biological
models, spatial ecology, reproducible experiments, committed scientific evidence, and
independent interactive/cinematic presentation.

The Reference Ecology and flagship scenarios are software/modeling demonstrations,
not empirically calibrated predictions about real populations.

## What the project demonstrates

- a frozen domain-neutral transactional simulation kernel with deterministic seeded
  RNG;
- a general-evolution layer demonstrated independently of biological organisms;
- compositional genetics, inheritance, development, energetics, behavior, feeding,
  predation, reproduction, and spatial ecology;
- explicit chromosome-copy, pairing, recombination, and segregation responsibilities
  without treating simple diploidy as universal architecture;
- arity-neutral reproduction orchestration separating participants, investors,
  genetic contributors, and offspring-production sources;
- committed population, spatial, genetic, pedigree/lifetime, and causal event
  evidence;
- exact checkpoint/resume and reproducible multi-seed experiments;
- a bounded Evolution Experiment Workbench with exact Study persistence, immutable
  fork lineage, Evidence Plans, controlled experiments, Results, and Presentation;
- a native PySide6 + Qt Quick/QML desktop product with off-GUI scientific execution,
  native scientific-world replay, keyboard/accessibility hardening, and standalone
  packaging proof;
- a deterministic B3 Manim cinematic path over the same validated scientific
  handoff;
- architecture, typing, testing, documentation, complexity, and CI guardrails.

## Quick start

```bash
git clone https://github.com/abdullahkhan57721/evolution-simulation-engine.git
cd evolution-simulation-engine
python3.12 -m venv venv
venv/bin/python -m pip install --upgrade pip
venv/bin/python -m pip install -e ".[dev,docs]"
```

Run core examples:

```bash
venv/bin/python examples/basic_aging_simulation.py
venv/bin/python examples/reference_ecology_simulation.py
```

Run the complete local quality gate:

```bash
./scripts/check_all --no-pause
```

## Native Evolution Experiment Workbench

PySide6 + Qt Quick/QML is the product frontend. Install the pinned desktop runtime:

```bash
venv/bin/python -m pip install -r requirements-desktop.txt
```

Launch the Workbench:

```bash
venv/bin/python -m evo_engine.desktop.main
```

The product flow is:

```text
New/Open Study
      ↓
Simulation → Evidence → Experiment
      ↓
Run Plan → Run
      ↓
Results → Interactive World → Presentation
      ↓
Save / Save As / Fork / Reproduce
```

Current concrete product families are controlled single-run Studies, E3 max-speed
sweeps, E4 environment-selection comparisons, canonical/derived B3, and bounded
Reference Ecology. The UI delegates exact scientific ownership to existing Workbench
artifacts/runners/inspectors rather than defining a Qt-specific Study or analysis
schema.

Native presentation includes committed-step world replay for Reference Ecology and a
matched side-by-side B3 replay using the renderer-neutral `WorldPresentationFrame`
contract. Playback, selection, labels, trails, Focus Mode, interpolation, and other
view choices never alter scientific identity.

Canonical B3 can also prepare the existing validated scientific cinematic handoff.
Scientific story eligibility is reported separately from optional Manim renderer
availability, and expensive rendering is dispatched off the GUI thread. A B3-derived
radius-2 fork cannot inherit canonical headline-cinematic eligibility.

See [Desktop Workbench](docs/desktop_workbench.md) and
[Q5 Frontend Parity](docs/development/q5_frontend_parity.md).

### Streamlit status

The former WU1–WU5 Streamlit/Plotly Workbench is **deprecated**. Its source remains
temporarily as frozen regression/reference material while native release auditing is
completed; it is no longer a product surface and receives no new feature work.
Future product milestones do not owe it parity.

Physical Streamlit/Plotly removal should happen as one bounded maintenance change
after the requested human native desktop/accessibility audit confirms the replacement
product and any remaining compatibility value is deliberately migrated or discarded.

## Confirmed scientific flagship — environment-dependent selection

The B3 flagship asks whether compact spatial resource geography changes selection on
existing heritable `max_speed` standing variation relative to a matched uniform
resource environment in the richer Reference Ecology.

The canonical comparison changes only renewable-resource placement:

```text
uniform placement
        versus
two equal-weight radius-1 patches
centered at (2, 5) and (9, 5)
```

Both arms use 20 balanced homozygous `max_speed = 1` / `4` founders, initial high-speed
allele frequency `0.50`, 32 renewable deposits per timestep, 6 units per deposit,
shared `max_intake_rate = 8`, mutation disabled, predation isolated through the
frozen attack/defense background, mating radius `3`, and 50 committed timesteps.

The frozen independent confirmation seeds are:

```text
5, 17, 29, 43, 61, 79, 97, 113
```

At the predeclared step-30 readout:

- mean uniform high-speed allele frequency: **0.3423**;
- mean compact radius-1 high-speed allele frequency: **0.6266**;
- mean paired compact-minus-uniform effect: **+0.2843**;
- compact exceeded matched uniform in **8/8** confirmation seeds.

Founder reproductive contribution, founder-label counterbalancing, and a radius-2
geometry sensitivity support and bound the interpretation. Representative seed 5 was
chosen by a predeclared median-effect/legible-episode rule rather than visual
convenience.

Run the frozen confirmation:

```bash
venv/bin/python scripts/b3_confirmation.py
```

See [Confirmed Flagship Evolution Demo](docs/flagship_evolution_demo.md) for the full
design, primary per-seed results, representative committed episodes, and
claim/nonclaim boundary.

### Supported claim

Under this tested Reference Ecology configuration, compact radius-1 resource
geography favors the high-speed strategy relative to matched uniform controls, while
uniform favors the lower-speed strategy in aggregate.

This does **not** establish universal optimal speed, generic effects of all patchy
environments, isolated locomotion-cost causality, or empirical species calibration.

## Deterministic cinematic presentation

Install Manim separately:

```bash
venv/bin/python -m pip install -r requirements-animation.txt
```

Render the existing generic deterministic portfolio animation:

```bash
venv/bin/python examples/render_portfolio_animation.py --quality low
```

Render the confirmed B3 explanatory flagship:

```bash
venv/bin/python examples/render_b3_flagship_cinematic.py \
  --quality high \
  --output outputs/b3-flagship-cinematic.mp4
```

A short real-B3 director excerpt is available for faster verification:

```bash
venv/bin/python examples/render_b3_flagship_cinematic.py \
  --excerpt \
  --quality low \
  --output outputs/b3-director-smoke.mp4
```

Simulation completes before Manim rendering. The director consumes the frozen
scientific handoff and authoritative committed evidence. Interpolation, camera,
timing, quality, output format, and choreography never feed back into simulation
semantics. Representative seed 5 is illustrative; independent multi-seed confirmation
remains the robustness evidence.

See [B3 Flagship Cinematic](docs/cinematic_flagship.md).

## Reproducible experiments and evidence

The project treats committed evidence and reproducibility as architecture rather than
presentation convenience:

```text
configured scientific context
        ↓
committed state + committed events
        ↓
scenario-specific measurements
        ↓
replicate/treatment summaries
        ↓
renderer-neutral scientific meaning
        ↓
interactive / cinematic presentation
```

Renewable-generation provenance comes from committed `ResourceGeneration` events.
Total committed world resources come from spatial state and may also include returned
resources; those meanings are deliberately not conflated. The experiment/export layer
supports deterministic replicate runs plus metadata/JSON/CSV export for reusable
scenarios.

## Architecture

The intended dependency direction is:

```text
validation / context / generic foundations
                    ↓
             simulation kernel
                    ↓
         general evolution abstractions
                    ↓
      biological/domain specializations
                    ↓
        processes and resolvers
                    ↓
       presets / experiments / interfaces
```

### Frozen transactional kernel

The kernel coordinates generic state transitions; it does not know about organisms,
genomes, reproduction, energy, ecology, or spatial worlds. Each stage preserves:

```text
propose all
→ resolve
→ materialize all accepted events
→ apply accepted events
```

Each step operates on transactional working state and transactional RNG. Only a fully
successful step becomes authoritative. New modeled behavior normally belongs above
the kernel unless a genuine generic deficiency is demonstrated.

### General evolution and biological specialization

The general layer models transmissible state, expression, variation, propagation,
linkage/co-transmission, production, admission/departure, and entity access/reference
without assuming DNA or organisms. Biological inheritance specializes those
contracts with genomes, genetic architecture, chromosome transmission, development,
and reproduction. Current clonal and biparental behavior are concrete policies over
more general orchestration contracts.

### Observation and presentation

```text
simulation/domain layers
        ↓
committed scientific evidence
        ↓
renderer-neutral scientific meaning
        ↓
   +---------+----------+
   |                    |
   v                    v
Qt Quick native       Manim
interactive product   cinematic explanation
```

Both presentation media consume immutable completed evidence. Neither is a second
simulation architecture.

## Documentation

Start with:

- [Current Project State](docs/development/current_state.md)
- [Architectural Roadmap](docs/development/roadmap.md)
- [Architecture Overview](docs/architecture/index.md)
- [Desktop Workbench](docs/desktop_workbench.md)
- [Q5 Frontend Parity](docs/development/q5_frontend_parity.md)
- [Scientific Visualization Architecture](docs/architecture/scientific_visualization.md)
- [Kernel Contract](docs/kernel_contract.md)
- [General Evolution Framework](docs/general_evolution_framework.md)
- [Reference Ecology](docs/reference_ecology.md)
- [Confirmed Flagship Evolution Demo](docs/flagship_evolution_demo.md)
- [B3 Flagship Cinematic](docs/cinematic_flagship.md)
- [Learning Guide](docs/learning/engine_guide/index.md)

The repository also contains subsystem documentation, ADRs, generated architecture
maps, manual-verification guidance, and a public MkDocs/GitHub Pages site.
