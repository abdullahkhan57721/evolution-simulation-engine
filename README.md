# Evolution Simulation Engine

Evolution Simulation Engine is a Python 3.12 simulation system for studying
heritable change in evolving populations without making biological assumptions
part of the execution kernel. A frozen domain-neutral transactional kernel sits
below general-evolution contracts, compositional biological models, spatial
ecology, reproducible experiments, and independent interactive/cinematic
presentation paths.

The reference ecology and flagship scenarios are software/modeling demonstrations,
not empirically calibrated predictions about real populations.

## What the project demonstrates

- a frozen domain-neutral transactional simulation kernel with deterministic
  seeded RNG;
- a general-evolution layer demonstrated independently of biological organisms;
- compositional genetics, inheritance, development, energetics, behavior, feeding,
  predation, reproduction, and spatial ecology;
- explicit chromosome-copy structure, pairing, recombination, and segregation
  responsibilities without treating simple diploidy as universal architecture;
- arity-neutral reproduction orchestration that separates participants, investors,
  genetic contributors, and offspring-production sources;
- committed population, spatial, genetic, pedigree/lifetime, and causal event
  evidence;
- exact checkpoint/resume and reproducible multi-seed experiments;
- JSON/CSV experiment export;
- an adaptive Streamlit/Plotly exploration path over completed immutable evidence;
- a deterministic Manim cinematic path, including a B3-specific explanatory
  flagship director, over the same evidence boundary;
- architecture, typing, testing, documentation, complexity, and CI guardrails.

## Quick start

```bash
git clone https://github.com/abdullahkhan57721/evolution-simulation-engine.git
cd evolution-simulation-engine
python3.12 -m venv venv
venv/bin/python -m pip install --upgrade pip
venv/bin/python -m pip install -e ".[dev,docs]"
```

Run the core examples:

```bash
venv/bin/python examples/basic_aging_simulation.py
venv/bin/python examples/reference_ecology_simulation.py
```

Run the complete local quality gate:

```bash
./scripts/check_all --no-pause
```

## Confirmed scientific flagship — environment-dependent selection

The current scientific flagship asks:

> Does compact spatial resource geography change selection on existing heritable
> `max_speed` standing variation relative to a matched uniform-resource
> environment in the current richer reference ecology?

The canonical matched comparison keeps the ordinary sexual reference ecology and
changes only renewable-resource placement:

```text
uniform placement
        versus
two equal-weight radius-1 patches
centered at (2, 5) and (9, 5)
```

Both arms use 20 balanced homozygous `max_speed = 1` / `4` founders, initial
high-speed allele frequency `0.50`, 32 renewable deposits per timestep, 6 units per
deposit, shared `max_intake_rate = 8`, mutation disabled, predation isolated
through the frozen attack/defense background, mating radius `3`, and 50 committed
timesteps.

Discovery and confirmation use disjoint seeds. The frozen independent confirmation
set is:

```text
5, 17, 29, 43, 61, 79, 97, 113
```

At the predeclared step-30 readout:

- mean uniform high-speed allele frequency: **0.3423**;
- mean compact radius-1 high-speed allele frequency: **0.6266**;
- mean paired compact-minus-uniform effect: **+0.2843**;
- compact exceeded matched uniform in **8/8** confirmation seeds.

Founder realized reproductive contribution supports the mechanism in aggregate,
and predeclared founder-label counterbalancing plus a radius-2 geometry sensitivity
provide bounded falsification checks. The representative storytelling seed is
**5**, chosen by a predeclared median-effect/legible-episode rule rather than visual
convenience.

Run the frozen confirmation:

```bash
venv/bin/python scripts/b3_confirmation.py
```

See [Confirmed Flagship Evolution Demo](docs/flagship_evolution_demo.md) for the
full frozen design, all primary per-seed results, scientific storyboard,
representative committed episodes, and claim/nonclaim boundary.

### Supported claim

Under this tested reference-ecology configuration, compact radius-1 resource
geography favors the high-speed strategy relative to matched uniform controls,
while uniform favors the lower-speed strategy in aggregate.

This does **not** establish universal optimal speed, generic effects of all patchy
environments, isolated locomotion-cost causality, or empirical species calibration.

## Earlier v0.1 max-intake demonstration

The original balanced-standing-variation `max_intake_rate` scenario remains a
secondary historical regression/integration example. Its helpers and current
presentation entry points are retained for compatibility with the v0.1 portfolio
surface.

The B3 cinematic path now consumes the confirmed scientific handoff directly. The
interactive B3 matched-comparison continuation should do the same rather than
infer B3 treatment/control meaning from the older max-intake example.

## Interactive Streamlit / Plotly application

Install the optional UI dependencies:

```bash
venv/bin/python -m pip install -r requirements-ui.txt
```

Launch the dashboard:

```bash
venv/bin/python -m streamlit run src/evo_engine/ui/app.py
```

The application separates a full-window configuration experience from a completed
world-centered simulation workspace. It provides committed-step playback,
selection/inspection, environmental layers, focal-trait visualization from
committed selective trait evidence, evolutionary/genetic analytics, life-history
views, experiment comparison, and export.

The UI never owns a mutable live engine/world after execution. Presentation values
remain downstream of committed simulation evidence.

The generic/science-aware foundation is ready for the dedicated B3 matched
comparison; renderer-specific B3 layout and interaction remain presentation work,
not part of the B3 scientific contract.

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

The simulation completes before Manim renders. The cinematic layer consumes
committed spatial/population/focal-trait evidence and authoritative committed event
telemetry through renderer-owned preparation values. The B3 director then consumes
the frozen scientific handoff to control scene order, camera focus, temporal
compression, matched comparison, evidence charts, and conclusion timing.
Interpolation, camera, timing, and choreography never feed back into simulation
semantics.

The B3 film keeps organism fill on the fixed `max_speed` scale `1..4`, body size on
authoritative body mass, and focus on a separate halo/camera channel. Representative
seed 5 is illustrative; independent confirmation remains run-level robustness
evidence. The render command also writes a deterministic scalar manifest beside the
video.

See [B3 Flagship Cinematic](docs/cinematic_flagship.md) for the full reproduction,
scientific-boundary, CI, and manual-review contract.

## Reproducible experiments and evidence

The project treats committed evidence and reproducibility as architectural
concerns rather than presentation conveniences.

B3 specifically separates:

```text
configured treatment context
        ↓
committed state + committed events
        ↓
scenario-specific scientific summaries
        ↓
matched multi-seed confirmation
        ↓
renderer-neutral scientific handoff
        ↓
interactive / cinematic presentation
```

Renewable-generation provenance comes from committed `ResourceGeneration` events.
Total committed world resources come from spatial state and can also include
resources returned through decomposition; those two meanings are deliberately not
conflated.

The ordinary experiment/export layer also supports deterministic replicate runs,
metadata, JSON, and CSV export for reusable scenarios.

## Architecture

The intended dependency direction is:

```text
validation / context / generic foundations
                    |
                    v
             simulation kernel
                    |
                    v
         general evolution abstractions
                    |
                    v
      biological/domain specializations
                    |
                    v
        processes and resolvers
                    |
                    v
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

Each step operates on transactional working state and transactional RNG. Only a
fully successful step becomes authoritative. New modeled behavior normally belongs
above the kernel unless a genuine generic deficiency is demonstrated.

### General evolution and biological specialization

The general layer models transmissible state, expression, variation, propagation,
linkage/co-transmission, production, admission/departure, and entity
access/reference without assuming DNA or organisms. Biological inheritance
specializes those contracts with genomes, genetic architecture, chromosome
transmission, development, and reproduction.

Shared reproduction is not universally one-parent or two-parent. Current simple
clonal and biparental sexual behavior are concrete policies over more general
orchestration contracts.

### Observation and presentation

```text
simulation/domain layers
        |
        v
committed scientific evidence
        |
        v
scenario-specific scientific meaning
        |
        +-------------------------+
        |                         |
        v                         v
Streamlit / Plotly             Manim
interactive exploration       cinematic explanation
```

Both presentation paths consume immutable completed evidence. Neither is a second
simulation architecture.

## Documentation

Start with:

- [Current Project State](docs/development/current_state.md)
- [Architectural Roadmap](docs/development/roadmap.md)
- [Architecture Overview](docs/architecture/index.md)
- [Scientific Visualization Architecture](docs/architecture/scientific_visualization.md)
- [Kernel Contract](docs/kernel_contract.md)
- [General Evolution Framework](docs/general_evolution_framework.md)
- [Reference Ecology](docs/reference_ecology.md)
- [Confirmed Flagship Evolution Demo](docs/flagship_evolution_demo.md)
- [B3 Flagship Cinematic](docs/cinematic_flagship.md)
- [Learning Guide](docs/learning/engine_guide/index.md)

The repository also contains subsystem documentation, ADRs, generated architecture
maps, manual-verification guidance, and a public MkDocs/GitHub Pages site.
