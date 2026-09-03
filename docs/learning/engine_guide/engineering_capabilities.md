# Engineering Capabilities Checklist

The finished textbook should leave you able to perform these tasks without relying
on memorized API lists.

## Architecture

- identify which layer owns a proposed concept;
- distinguish contract from implementation;
- explain dependency direction and composition choices;
- estimate public-contract change radius;
- spot biology/domain leakage into generic layers.

## Runtime semantics

- trace one complete run/step/stage;
- distinguish committed and working state;
- predict same-stage state visibility;
- place stochastic work in the correct phase;
- explain commit and rollback behavior.

## Evolution modeling

- explain evolution using transmissible state rather than biological vocabulary;
- map general propagation/expression/variation/linkage onto biology;
- distinguish propagation from production;
- distinguish reproductive participants, investors, contributors, and production
  sources.

## Code reading

- read public contract → focused test → implementation;
- separate semantic code from validation/performance plumbing;
- identify mutation and authority;
- summarize a file as purpose → invariant → algorithm → tradeoff.

## Complexity and memory

- define scale variables;
- express delegated costs honestly;
- reason about time and auxiliary space;
- track memory lifetime and historical retention;
- perform 10x scaling thought experiments.

## Performance

- distinguish Big-O, profiling, benchmarking, and allocation measurement;
- identify the correct layer before optimizing;
- distinguish measured hotspots from theoretical hazards;
- review time-space tradeoffs and semantics-sensitive caching;
- know when to stop optimizing.

## Quality review

- evaluate readability using concrete criteria;
- evaluate maintainability by change radius/duplication/semantic paths;
- distinguish extensibility from speculative abstraction;
- identify architecture smells and healthy patterns;
- review a PR across correctness, performance, memory, readability,
  maintainability, extensibility, and testability.

## Design

- fill out the architecture worksheet for a new feature;
- determine whether an existing contract can express it;
- justify a lower-layer change with generic evidence when necessary;
- derive a minimal kernel from required semantics;
- explain the engine without class names.
