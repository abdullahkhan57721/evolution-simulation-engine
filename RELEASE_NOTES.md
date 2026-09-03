# Evolution Simulation Engine v0.1.0

v0.1.0 is the first portfolio release of Evolution Simulation Engine. It freezes a
reviewer-facing baseline around the architecture already proven in the repository:
a domain-neutral transactional kernel, general-evolution abstractions,
compositional biological/ecological models, reproducible experiments, and two
downstream presentation paths.

## Highlights

- **Domain-neutral simulation kernel:** deterministic transactional state/RNG
  execution with stage-start proposal simultaneity and committed telemetry.
- **General evolution layer:** transmissible-state expression, variation,
  propagation, production, access/reference, and lifecycle foundations that are
  demonstrated without biological simulation objects.
- **Compositional biology:** genetics, inheritance, development, energetics,
  feeding, behavior, movement, predation, reproduction, and spatial ecology above
  the generic layers.
- **Reproduction architecture:** arity-neutral participant groups with separate
  investor, genetic-contributor, and offspring-production-source responsibilities.
- **Chromosome transmission architecture:** explicit chromosome-copy structure,
  pairing, recombination, segregation, and gamete-formation responsibilities while
  preserving current Mendelian behavior.
- **Reproducibility:** seeded execution, exact checkpoint/resume, multi-seed
  experiments, and JSON/CSV export.
- **Committed evidence:** population, spatial, genetic, pedigree/lifetime, and
  causal event/effect records.
- **Interactive portfolio UI:** Streamlit/Plotly configuration, spatial playback,
  evolutionary/genetic analytics, experiment comparison, and downloads.
- **Adaptive configuration:** conditional mutation/recombination controls normalize
  into real typed engine configuration; hidden form state cannot leak into a run.
- **Cinematic replay:** optional Manim renderer driven only by committed
  renderer-neutral observations after simulation completion.
- **Flagship evolutionary demonstration:** a reproducible standing-variation
  `max_intake_rate` selection story with one canonical seed and an eight-seed
  robustness set.
- **Engineering discipline:** Ruff, Pyright, Import Linter, frozen-kernel
  contracts, Complexipy, pytest/coverage, strict MkDocs, performance checks,
  protected CI, headless Streamlit tests, and isolated real Manim render/decode
  smoke coverage.

## Flagship demonstration

The flagship scenario begins with balanced homozygous founder variation at the
existing `max_intake_rate` locus. The high-intake allele starts at frequency
`0.50`. Mutation is disabled and predation is isolated for interpretability while
the normal resource acquisition, energetics, survival, sexual reproduction,
inheritance, and observation machinery remains active.

The canonical fixed run uses seed `41` for `40` steps. The canonical robustness set
is:

```text
11, 23, 37, 41, 59, 73, 89, 101
```

Protected tests require every canonical run to remain alive through the 40-step
window and finish with the high-intake allele above its initial `0.50` frequency.
The scenario is an illustrative software/modeling demonstration, not an empirical
prediction of a real ecosystem.

## Install and explore

The repository requires Python 3.12. Core installation, dashboard launch,
experiments/export, and Manim render commands are documented in `README.md`.
Public documentation is deployed at:

https://abdullahkhan57721.github.io/evolution-simulation-engine/

## License

v0.1.0 is released under the MIT License.

## Known scope limits

This release does not claim scientific calibration, production polyploid meiosis,
exhaustive mating systems, or a native Rust/C++ execution backend. Current simple
chromosome pairing/recombination policies intentionally implement the biology used
by the shipped simulations while the public architecture leaves room for richer
future policies.
