# Learning the Evolution Simulation Engine

This textbook explains the Evolution Simulation Engine as a set of ideas first and
as Python code second. Its goal is not merely to tell you which method to call. It
is to make the architecture understandable enough that you can open the source,
recognize the responsibilities and invariants you are looking at, and reason about
new design work without relying on memorized diagrams.

> **This guide is pedagogical, not authoritative.** The executable repository,
> [Simulation Kernel Contract](../../kernel_contract.md),
> [General Evolution Framework](../../general_evolution_framework.md), architecture
> docs, ADRs, and focused tests define the actual project. If this guide ever
> disagrees with those sources, fix the guide.

## The central picture

The engine separates three questions that are easy to mix together:

```text
                    BIOLOGICAL SPECIALIZATION
              What does this mean biologically?
                           |
                           v
                    GENERAL EVOLUTION
              What makes this evolutionary?
                           |
                           v
                  SIMULATION KERNEL
          How do state transitions execute safely,
          reproducibly, and transactionally?
```

Architecturally, dependencies point upward from generic foundations toward richer
domain meaning. Pedagogically, we will sometimes start with the scientific idea
and then look downward to the machinery that executes it.

## Choose a learning path

### First time learning the architecture

Read in this order:

1. [Software Architecture Primer](architecture_primer.md)
2. [Simulation Fundamentals](simulation_fundamentals.md)
3. [General Evolution](general_evolution.md)
4. [Biological Specialization](biological_specialization.md)
5. [Kernel Mental Model](kernel_mental_model.md)
6. [Kernel Public API](kernel_public_api.md)
7. [Kernel Runtime](kernel_runtime.md)
8. [Kernel Design Rationale and Invariants](kernel_design_rationale.md)
9. [Worked Examples Across the Layers](worked_examples.md)
10. [Reading the Kernel Source](source_code_walkthrough.md)

Then use the [Debugger Labs](debugger_labs.md) and [Exercises](exercises.md) to
turn recognition into working understanding.

### I want to understand the kernel now

Start with:

1. [Kernel Mental Model](kernel_mental_model.md)
2. [Kernel Public API](kernel_public_api.md)
3. [Kernel Runtime](kernel_runtime.md)
4. [Kernel Design Rationale and Invariants](kernel_design_rationale.md)
5. [Reading the Kernel Source](source_code_walkthrough.md)

Keep the [Cheat Sheet](cheatsheet.md) open beside the source.

### I am reading code and I am lost

Use this order:

1. [Cheat Sheet](cheatsheet.md) — identify the layer and responsibility.
2. [Glossary](glossary.md) — disambiguate terminology.
3. [Reading the Kernel Source](source_code_walkthrough.md) — find the recommended
   file and reading order.
4. [Kernel Runtime](kernel_runtime.md) — place the code in the call flow.

### I want to understand evolution or reproduction

Read:

1. [General Evolution](general_evolution.md)
2. [Biological Specialization](biological_specialization.md)
3. [Worked Examples Across the Layers](worked_examples.md)

The important conceptual bridge is:

```text
transmissible state -> genome
propagation         -> biological inheritance
variation           -> mutation / recombination
entity production   -> biological offspring production
```

Those are **specializations**, not synonyms.

### I want to practice

Go to:

1. [Debugger Labs](debugger_labs.md)
2. [Exercises](exercises.md)
3. [Reading the Kernel Source](source_code_walkthrough.md)

The exercises emphasize prediction, comparison, and implementation rather than
terminology recall.

## Concept dependency graph

The textbook is organized around dependencies among ideas rather than the order
of Python files:

```text
abstraction / contracts / composition
                |
                v
state transitions and side effects
                |
                v
transactions + determinism + ownership
                |
                v
stages + conflicts + observation
                |
                +-------------------------------+
                |                               |
                v                               v
        simulation kernel               evolutionary semantics
                                                |
                                                v
                         transmissible state / expression /
                         propagation / variation / linkage /
                         production / persistence / selection
                                                |
                                                v
                                   biological specialization
```

You do not need every software-architecture term memorized before moving on. The
guide deliberately revisits important ideas at increasing depth.

## Master architecture map

```text
                                   COMPOSITION
                       presets / experiments / interfaces
                                     |
                                     v
                              SimulationSpec
                         generic preflight / compile
                                     |
                      +--------------+--------------+
                      |                             |
                      v                             v
                 Simulation                  SimulationEngine
                      |                             |
                      |                             +-- stopping condition
                      |                             +-- observers
                      |                             +-- telemetry observers
                      |                             |
                      v                             v
              SimulationState            SequentialStepCoordinator
          +-----------+-----------+                  |
          |           |           |                  v
          v           v           v           StageCoordinator(s)
     domain_state   context      RNG                   |
          |                                              |
          |                          +-------------------+-------------------+
          |                          |                   |                   |
          |                          v                   v                   v
          |                      Processes           Resolver           telemetry
          |                   propose / apply      choose events         records
          |                   materialize?
          |
          +---------------------------------------------------------------+
                                  domain mutation
```

The most important ownership fact is easy to miss:

```text
Simulation owns the authoritative SimulationState.
SimulationEngine does not.
```

The engine asks the step coordinator for a completed transactional state and only
then replaces `simulation.state`.

## The three-example ladder

We will use the same architecture at three levels:

```text
1. Counter
   kernel only
   proves generic execution

2. Information network
   kernel + general evolution
   proves evolution without biology

3. Biological simulation
   kernel + general evolution + biology
   proves specialization
```

When a concept feels complicated, ask which of those three levels actually needs
it.

## A reading habit to develop

When you encounter unfamiliar code, ask two questions rather than one:

1. **What does this Python execute?**
2. **Why does this line exist architecturally?**

For example:

```python
working_state = simulation_state.copy()
```

At the syntax level, this calls `copy()`.

At the architecture level, it establishes the transaction boundary: the step can
mutate modeled state and consume randomness without touching the committed state
unless the complete step succeeds.

That second kind of reading is the main skill this textbook is designed to teach.

## Authoritative companions

Keep these nearby:

- [Simulation Kernel Contract](../../kernel_contract.md)
- [General Evolution Framework](../../general_evolution_framework.md)
- [Architecture Overview](../../architecture/index.md)
- [Architecture Decisions](../../decisions/README.md)
- [`tests/engine/test_stage_coordinator.py`](https://github.com/abdullahkhan57721/evolution-simulation-engine/blob/main/tests/engine/test_stage_coordinator.py)
- [`tests/engine/test_domain_neutral_kernel.py`](https://github.com/abdullahkhan57721/evolution-simulation-engine/blob/main/tests/engine/test_domain_neutral_kernel.py)

## What success looks like

You do **not** need to memorize every class.

You understand the engine when you can look at a proposed behavior and answer:

- Which layer owns its meaning?
- What state does it need to read?
- When is it allowed to consume randomness?
- Does it propose, resolve, materialize, apply, or observe?
- Who is allowed to mutate the domain?
- What invariant would be violated by the obvious simpler implementation?
- Which focused test should prove the behavior?

If those questions become natural, the source code becomes much easier to read.
