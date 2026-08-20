# Architecture Guardrails

The repository uses Import Linter contracts in `pyproject.toml` to protect a small set of dependency boundaries that are intended to remain stable as the simulation engine grows.

The current contracts enforce these principles:

- `evo_engine.validation` is a dependency foundation and must not depend on simulation-domain packages.
- `evo_engine.genetics` remains upstream of development, energetics, engine orchestration, growth, processes, reproduction, resolvers, spatial behavior, and world state.
- Domain packages (`development`, `energetics`, `genetics`, `growth`, `reproduction`, `spatial`, and `world`) must not depend on concrete process or resolver implementations.
- Engine orchestration must not depend on concrete process or resolver implementations.

These contracts deliberately do not attempt to encode the entire package graph. New contracts should be added only when a dependency direction is an intentional architectural invariant rather than an incidental property of the current implementation.

Run the architecture check locally with:

```bash
./scripts/architecture
```

The same check runs in GitHub Actions as part of the repository quality gate.
