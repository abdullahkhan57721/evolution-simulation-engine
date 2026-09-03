# Evolution Simulation Engine

Evolution Simulation Engine is a Python 3.12 system for constructing and studying
evolutionary simulations while keeping execution mechanics separate from modeled
meaning. Its frozen domain-neutral kernel provides deterministic transactional
execution; general-evolution abstractions and biological/ecological specializations
live above that boundary.

The **v0.1.0 portfolio release** demonstrates the architecture through a complete
spatial ecology, reproducible evolutionary experiments, an interactive
Streamlit/Plotly dashboard, and a deterministic Manim cinematic driven by the same
committed observation data.

The reference ecology and flagship demonstration are illustrative engine examples,
not calibrated predictions of a real ecosystem.

## Explore the v0.1.0 release

### Run the flagship evolutionary story

Start with [Flagship Evolution Demo](flagship_evolution_demo.md) to see how standing
variation at the existing `max_intake_rate` locus flows through resource
acquisition, survival/reproduction, inheritance, and measured allele-frequency
change.

The canonical demonstration uses one fixed seed for a reproducible walkthrough and
a canonical eight-seed set for robustness evidence.

### Use the interactive dashboard

The Streamlit/Plotly interface provides spatial playback, population and ecological
summaries, heritable-trait trajectories, allele/genotype frequencies, event and
mortality views, pedigree/lifetime contribution, experiments, and JSON/CSV export.

From the repository root:

```bash
python3.12 -m venv venv
venv/bin/python -m pip install --upgrade pip
venv/bin/python -m pip install -e ".[dev,docs]"
venv/bin/python -m pip install -r requirements-ui.txt
venv/bin/python -m streamlit run src/evo_engine/ui/app.py
```

Choose **Run flagship evolution demo** for the canonical portfolio scenario.

### Render the cinematic replay

Install the optional animation stack and render the same flagship evidence through
Manim:

```bash
venv/bin/python -m pip install -r requirements-animation.txt
venv/bin/python examples/render_portfolio_animation.py --quality low
```

The simulation completes before rendering begins. Manim consumes committed
renderer-neutral observation values rather than owning or driving a live
simulation.

### Run reproducible experiments

Read [Reproducible Experiments and Export](experiments.md) for the multi-seed API,
run metadata, JSON/CSV persistence, and checkpoint/resume workflow.

## Understand the architecture

A good technical-review reading order is:

1. [Architecture Overview](architecture/index.md) — package/layer map and reading
   order.
2. [Simulation Kernel Contract](kernel_contract.md) — frozen generic execution
   semantics.
3. [General Evolution Framework](general_evolution_framework.md) — evolution
   concepts without biological assumptions.
4. [Reference Ecology](reference_ecology.md) — high-level biological/ecological
   composition.
5. [Flagship Evolution Demo](flagship_evolution_demo.md) — the end-to-end v0.1
   story.
6. [Architecture Decision Records](decisions/README.md) — rationale for major
   settled choices.

The core dependency direction is:

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

Presentation remains downstream:

```text
simulation/domain layers
        |
        v
committed observation / experiment values
        |
        +-------------------------+
        |                         |
        v                         v
Streamlit / Plotly             Manim
```

## Learn the engine deeply

The [Learning Guide](learning/engine_guide/index.md) is a repository-native
textbook covering software architecture, simulation fundamentals, general
evolution, biological specialization, the kernel runtime, source-code reading,
complexity/performance analysis, debugging, review workflows, and design
exercises.

It is deliberately pedagogical rather than authoritative. Current code, tests,
architecture documents, and ADRs remain the source of truth.

## Quality and development

The repository enforces Ruff, Pyright, Import Linter architecture contracts,
kernel-contract regressions, Complexipy, pytest/coverage, strict MkDocs, and
reference/kernel performance checks through protected CI. The dashboard also has
headless Streamlit interaction coverage, while Manim has an isolated real
render/decode smoke workflow.

For contributor and agent workflow, see the root `AGENTS.md` and
`CONTRIBUTING.md`. For current orientation and post-v0.1 direction, see:

- [Current Project State](development/current_state.md)
- [Architectural Roadmap](development/roadmap.md)

## API reference

- [Validators API](references/validators.md)
