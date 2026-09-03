# Evolution Simulation Engine

Evolution Simulation Engine is a Python 3.12 simulation system for studying
heritable change in evolving populations without making biological assumptions
part of the execution kernel. A frozen domain-neutral transactional kernel sits
below general-evolution contracts, compositional biological models, spatial
ecology, reproducible experiments, and two independent presentation paths:
Streamlit/Plotly for interactive exploration and Manim for deterministic cinematic
replay.

**v0.1.0 is a portfolio release focused on proving that architecture end to end.**
Its flagship demonstration starts with standing genetic variation in resource
intake capacity, runs the ordinary spatial ecology and inheritance machinery, and
measures the resulting change in population genetic composition across a fixed
seed and a canonical multi-seed robustness set.

The reference ecology and flagship scenario are software/modeling demonstrations,
not empirically calibrated ecological predictions.

## What v0.1.0 demonstrates

- a domain-neutral transactional simulation kernel with deterministic seeded RNG;
- a general-evolution layer demonstrated independently of biological organisms;
- compositional genetics, inheritance, reproduction, development, energetics,
  behavior, feeding, predation, and spatial ecology;
- arity-neutral shared reproduction orchestration that separates reproductive
  participants, investors, genetic contributors, and offspring-production sources;
- explicit chromosome-copy structure, pairing, recombination, and segregation
  responsibilities without making ordinary diploidy a universal architecture rule;
- committed population, spatial, genetic, pedigree/lifetime, and causal event
  observations;
- exact checkpoint/resume behavior and reproducible multi-seed experiments;
- JSON and CSV experiment export;
- an adaptive Streamlit/Plotly dashboard built only from typed configuration and
  committed result values;
- a deterministic Manim renderer built from the same committed evidence boundary;
- architecture, typing, testing, documentation, complexity, and CI guardrails.

## Quick start

Clone the repository and create a clean Python 3.12 environment:

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

The commands above use the repository convention for macOS/Linux virtual
environments. On Windows, use the corresponding `venv\Scripts\python` executable.

## Flagship evolutionary demonstration

The v0.1 flagship asks a deliberately narrow question:

> How can standing heritable differences in resource-acquisition capacity change a
> population under repeated spatially distributed resource opportunities?

The canonical run starts with 20 homozygous founders split evenly between
`max_intake_rate = 2` and `max_intake_rate = 8`, so the high-intake allele begins
at frequency `0.50`. Mutation is disabled and predation is isolated for causal
clarity. The ordinary reference ecology still owns resource acquisition,
energetics, movement, survival, sexual reproduction, inheritance, and observation.

The canonical configuration uses seed `41` for `40` steps. The canonical robustness
set is:

```text
11, 23, 37, 41, 59, 73, 89, 101
```

Across that measured set, every run used for the release demonstration remains
alive through the 40-step window and finishes with the high-intake allele above
its initial `0.50` frequency. Tests intentionally protect qualitative behavior
rather than fragile exact stochastic totals.

Run the canonical scenario directly:

```python
from evo_engine.presets import build_flagship_max_intake_ecology

ecology = build_flagship_max_intake_ecology()
ecology.engine.run(ecology.simulation)

print(ecology.recorder.latest)
```

See [Flagship Evolution Demo](docs/flagship_evolution_demo.md) for the full causal
narrative, configuration, evidence, and claim boundaries.

## Interactive Streamlit / Plotly dashboard

Install the optional UI dependencies:

```bash
venv/bin/python -m pip install -r requirements-ui.txt
```

Launch the dashboard:

```bash
venv/bin/python -m streamlit run src/evo_engine/ui/app.py
```

The dashboard provides:

- one-click execution of the flagship scenario;
- curated typed reference-ecology configuration;
- conditional mutation and recombination controls whose hidden values cannot leak
  into engine configuration;
- immutable spatial world playback;
- population/ecological summaries;
- heritable-trait trajectories;
- allele and genotype frequencies;
- committed event activity and mortality outcomes;
- pedigree/lifetime reproductive-success views;
- multi-seed experiment comparison;
- JSON/CSV downloads using the existing experiment-export contracts.

The dashboard never owns a mutable live engine or world after execution. Its
presentation values are downstream of committed simulation evidence.

## Reproducible experiments and export

Run the canonical flagship robustness set and export it with the public experiment
API:

```python
from evo_engine.experiments import (
    run_flagship_max_intake_replicates,
    write_experiment_json,
    write_population_history_csv,
    write_replicate_summary_csv,
)

result = run_flagship_max_intake_replicates()

write_experiment_json(result, "outputs/flagship-experiment.json")
write_replicate_summary_csv(result, "outputs/flagship-summary.csv")
write_population_history_csv(result, "outputs/flagship-history.csv")
```

Experiment metadata records the seed, engine version, Python version, completed
steps, and tracked traits so runs remain inspectable rather than becoming opaque
arrays of outputs.

## Deterministic Manim cinematic

Manim is an optional sibling presentation path, not a replacement for the
interactive dashboard. Install it separately:

```bash
venv/bin/python -m pip install -r requirements-animation.txt
```

Render the fixed-seed flagship demonstration:

```bash
venv/bin/python examples/render_portfolio_animation.py --quality low
```

By default the result is written to `outputs/portfolio-animation.mp4`. The
simulation completes before Manim is imported for rendering. The renderer consumes
committed `SpatialObservation` and `PopulationObservation` histories through a
renderer-owned timeline; animation interpolation never feeds back into simulation
semantics.

CI contains an isolated cinematic smoke workflow that installs Manim, renders a
real low-quality MP4, and decodes a frame without making the heavy animation stack
a mandatory runtime dependency.

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
genomes, reproduction, energy, ecology, or spatial worlds. Its durable stage
contract is:

```text
propose all
→ resolve
→ materialize all accepted events
→ apply accepted events
```

Each step operates on a transactional working state and transactional RNG. Only a
fully successful step becomes authoritative. New modeled behavior normally belongs
above the kernel unless a genuine generic deficiency is demonstrated.

### General evolution and biological specialization

The general layer models concepts such as transmissible state, expression,
variation, propagation, linkage/co-transmission, production, admission/departure,
and entity access/reference without assuming DNA or organisms. Biological
inheritance specializes those contracts with genomes, genetic architecture,
chromosome transmission, development, and reproduction.

Shared reproduction is not universally “one-parent” or “two-parent.” Reproductive
participants may have arbitrary nonempty arity; concrete inheritance and mating
policies impose the stronger source-count rules they actually require. Current
simple clonal and biparental sexual models remain supported concrete policies.

### Observation and presentation

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
interactive exploration       cinematic replay
```

Both presentation paths consume immutable committed evidence. Neither is a second
simulation architecture.

## Documentation and learning guide

The public MkDocs site is deployed through GitHub Pages:

- **Documentation:** https://abdullahkhan57721.github.io/evolution-simulation-engine/
- [Architecture index](docs/architecture/index.md)
- [Simulation kernel contract](docs/kernel_contract.md)
- [General evolution framework](docs/general_evolution_framework.md)
- [Reference ecology](docs/reference_ecology.md)
- [Flagship evolution demo](docs/flagship_evolution_demo.md)
- [Reproducible experiments and export](docs/experiments.md)
- [Repository-native learning guide](docs/learning/engine_guide/index.md)
- [Contributor workflow](CONTRIBUTING.md)

The learning guide is pedagogical and intentionally subordinate to current code,
tests, authoritative architecture documentation, and ADRs.

## Quality and reproducibility

The repository quality gate includes:

- Ruff linting and formatting verification;
- Pyright static typing;
- Import Linter architecture contracts;
- frozen-kernel contract regressions;
- Complexipy cognitive-complexity limits;
- pytest with line and branch coverage;
- strict MkDocs builds;
- reference-ecology and domain-neutral kernel performance/profile checks;
- headless Streamlit interaction tests;
- an isolated Manim render/decode smoke workflow.

`main` is protected by a repository ruleset that requires pull requests and the
stable aggregate CI status before merge.

## Project scope

v0.1.0 is deliberately a foundation-and-demonstration release. It does **not**
claim scientific calibration, production polyploid meiosis, exhaustive mating
systems, or a native Rust/C++ execution backend. The architecture is designed so
richer genetics, mating systems, development/G×E, and evolutionary ecology can be
added above the settled lower boundaries when concrete use cases justify them.

See [Current Project State](docs/development/current_state.md) and the
[Architectural Roadmap](docs/development/roadmap.md) for the current development
front.

## License

Released under the [MIT License](LICENSE).
