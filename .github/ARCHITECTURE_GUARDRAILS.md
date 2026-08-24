# Architecture Guardrails

The repository uses Import Linter contracts in `pyproject.toml` to protect a small set of dependency boundaries that are intended to remain stable as the simulation engine grows.

The current contracts enforce these principles:

- `evo_engine.validation` is a dependency foundation and must not depend on simulation-domain packages or high-level presets.
- `evo_engine.genetics` remains upstream of behavior, development, energetics, engine orchestration, feeding, growth, life history, presets, processes, reproduction, resolvers, spatial behavior, and world state.
- Domain packages (`behavior`, `development`, `energetics`, `feeding`, `genetics`, `growth`, `life_history`, `reproduction`, `spatial`, and `world`) must not depend on concrete process or resolver implementations or on high-level presets.
- Engine orchestration must not depend on concrete process or resolver implementations or on high-level presets.

`evo_engine.life_history` contains cross-process organism strategy abstractions, such as reusable organism-specific threshold models. It is intentionally upstream of behavior, energetics, and reproduction policies that consume those abstractions. It should not become an orchestration layer or a dependency on concrete simulation processes.

`evo_engine.feeding` contains reusable feeding-physiology policies such as intake capacity and assimilation. It may depend on upstream genetic vocabulary and validation, but it must remain independent of the concrete `ResourceConsumption` process and resource-allocation resolvers. This keeps physiology reusable across future feeding processes and trophic models.

`evo_engine.presets` is an intentional **composition root**. It may depend on engine orchestration, domains, concrete processes, and resolvers in order to assemble complete simulations. Dependencies must point into the preset from user/example code, not back from lower-level engine or domain packages. This keeps convenient high-level configurations from becoming architectural dependencies of reusable components.

These contracts deliberately do not attempt to encode the entire package graph. New contracts should be added only when a dependency direction is an intentional architectural invariant rather than an incidental property of the current implementation.

Run the architecture check locally with:

```bash
./scripts/architecture
```

The same check runs in GitHub Actions as part of the repository quality gate.
