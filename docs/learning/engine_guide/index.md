# Learning the Evolution Simulation Engine

This textbook teaches the Evolution Simulation Engine as a set of ideas first and
as Python code second. The goal is not merely to know which method to call. The
goal is to be able to open the repository, identify responsibilities and
invariants, predict runtime behavior, analyze computational cost, and judge
whether a proposed change belongs in the kernel, the general-evolution layer, or
a biological specialization.

> **This guide is pedagogical, not authoritative.** Current code, tests,
> [Simulation Kernel Contract](../../kernel_contract.md),
> [General Evolution Framework](../../general_evolution_framework.md), architecture
> documentation, and ADRs define the project. If this textbook disagrees with
> them, fix the textbook.

## The central picture

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
          How do transitions execute safely,
          reproducibly, and transactionally?
```

The textbook adds a second axis that cuts across those layers:

```text
correctness -> semantics -> complexity -> measured performance
            -> readability -> maintainability -> extensibility -> testability
```

You should eventually be able to use both axes at once.

## The five-part course

### Part I — Think like a software engineer

1. [Software Architecture Primer](architecture_primer.md)
2. [Architecture Quality](architecture_quality.md)
3. [Computational Complexity and Performance Thinking](computational_complexity.md)

This part gives you the vocabulary and reasoning tools for abstraction,
dependencies, state, transactions, complexity, memory, profiling, readability,
and maintainability.

### Part II — Think like a simulation designer

4. [Simulation Fundamentals](simulation_fundamentals.md)

This chapter derives stages, conflicts, simultaneity, stochasticity, committed
versus working state, and observation from the needs of a general simulation.

### Part III — Think like an evolution modeler

5. [General Evolution](general_evolution.md)
6. [Biological Specialization](biological_specialization.md)

This part explains transmissible state, expression, realization, propagation,
variation, linkage, production, persistence, selection, and how biology
specializes those ideas.

### Part IV — Understand this engine

7. [Kernel Mental Model](kernel_mental_model.md)
8. [Kernel Public API](kernel_public_api.md)
9. [Kernel Runtime Walkthrough](kernel_runtime.md)
10. [Kernel Design Rationale and Invariants](kernel_design_rationale.md)
11. [How the Architecture Evolved](architecture_evolution.md)
12. [Engineering Anatomy of the Kernel](kernel_engineering_anatomy.md)
13. [Performance Case Studies](performance_case_studies.md)
14. [Worked Examples Across the Layers](worked_examples.md)
15. [Reading the Kernel Source](source_code_walkthrough.md)

### Part V — Prove you understand it

16. [Debugger Labs](debugger_labs.md)
17. [Architecture and Kernel Exercises](exercises.md)
18. [Complexity and Performance Exercises](complexity_exercises.md)
19. [Reasoning About Proposed Changes](change_reasoning.md)
20. [Review Workflows and Worksheets](review_workflows.md)
21. [Capstone Challenges](capstones.md)

Reference pages are available for [Architecture Smells and Healthy
Counterpatterns](design_smells_reference.md), the [Glossary](glossary.md), and the
[Cheat Sheet](cheatsheet.md).

## Choose a shorter learning path

### I want to understand the kernel now

Read:

1. [Kernel Mental Model](kernel_mental_model.md)
2. [Kernel Runtime Walkthrough](kernel_runtime.md)
3. [Kernel Public API](kernel_public_api.md)
4. [Reading the Kernel Source](source_code_walkthrough.md)
5. [Engineering Anatomy of the Kernel](kernel_engineering_anatomy.md)

Keep the [Cheat Sheet](cheatsheet.md) open only after your first pass.

### I am reading code and I am lost

Use this sequence:

```text
identify the layer
    -> identify the public responsibility
    -> find the focused test
    -> locate the top-level control flow
    -> separate semantics from support plumbing
    -> ask what is read, mutated, owned, and decided
```

Then use [Reading the Kernel Source](source_code_walkthrough.md) and
[Review Workflows and Worksheets](review_workflows.md).

### I want to understand evolution or reproduction

Read:

1. [General Evolution](general_evolution.md)
2. [Biological Specialization](biological_specialization.md)
3. [Worked Examples Across the Layers](worked_examples.md)

Remember this abstraction ladder:

```text
transmissible state -> genome
propagation         -> biological inheritance
variation           -> mutation / recombination
entity production   -> biological offspring production
```

Those are specializations, not synonyms.

### I want to understand performance

Read:

1. [Computational Complexity and Performance Thinking](computational_complexity.md)
2. [Engineering Anatomy of the Kernel](kernel_engineering_anatomy.md)
3. [Performance Case Studies](performance_case_studies.md)
4. [Complexity and Performance Exercises](complexity_exercises.md)

The central habit is:

> **Reason about scaling early; optimize implementation details when evidence
> justifies them.**

### I want to review a future PR

Use:

1. [Reasoning About Proposed Changes](change_reasoning.md)
2. [Review Workflows and Worksheets](review_workflows.md)
3. [Architecture Smells and Healthy Counterpatterns](design_smells_reference.md)
4. [Capstone Challenges](capstones.md)

## How to study the textbook

Use three passes rather than one passive read.

### Pass 1 — Build the conceptual skeleton

Read the foundations, simulation fundamentals, general evolution, biological
specialization, and kernel mental model. Your goal is to redraw these from
memory:

```text
three architectural layers
ownership graph
one-step transaction
one-stage phase order
general-evolution loop
```

### Pass 2 — Connect concepts to production source

Read the API, runtime, examples, engineering anatomy, and source walkthrough.
For every important line ask:

```text
What does this Python execute?
Why does this line exist architecturally?
```

Then add the engineering questions:

```text
How often does it execute?
How does cost scale?
What is allocated and for how long?
Is this actually measured hot?
Would a faster alternative damage readability or semantics?
```

### Pass 3 — Retrieve and apply

Use the debugger labs, exercises, review worksheet, and capstones with the guide
closed whenever possible. Predict first. Check afterward.

A few days later, use only the [Cheat Sheet](cheatsheet.md). If you recognize a
line but cannot reconstruct why it is true, return to the deeper chapter.

## Concept dependency graph

```text
abstraction / contracts / composition
                |
                v
state / mutation / side effects
                |
                +----------------------+
                |                      |
                v                      v
transactions / determinism      complexity / memory
                |                      |
                v                      v
stages / conflicts / observation   performance evidence
                |                      |
                +----------+-----------+
                           |
                           v
                  simulation kernel
                           |
                           v
                 general evolution
                           |
                           v
             biological specialization
```

## Master architecture map

```text
                              SimulationSpec
                         preflight / compilation
                                  |
                    +-------------+-------------+
                    |                           |
                    v                           v
               Simulation                SimulationEngine
                    |                           |
                    v                           v
            SimulationState          SequentialStepCoordinator
       +------------+-----------+                |
       |            |           |                v
       v            v           v         StageCoordinator(s)
  domain_state   context       RNG                |
                                               +-- Process(es)
                                               +-- Resolver
                                               `-- telemetry
```

The most important ownership fact is:

```text
Simulation owns the authoritative SimulationState.
SimulationEngine orchestrates its replacement; it does not own the state.
```

## The three-example ladder

```text
1. Counter
   kernel only

2. Information network
   kernel + general evolution

3. Biological simulation
   kernel + general evolution + biology
```

When an abstraction feels complicated, ask which level actually needs it.

## Five levels of mastery

Use this progression for the major ideas:

```text
1. RECOGNIZE  — I know what I am looking at.
2. EXPLAIN    — I can explain why it exists.
3. PREDICT    — I can predict system behavior.
4. DIAGNOSE   — I can find a violation or bad design.
5. DESIGN     — I can choose the correct boundary and solution myself.
```

The final capstones target level 5.

## What success looks like

You understand this engine when you can inspect unfamiliar code or a proposed
feature and answer:

- Which layer owns the meaning?
- What state is visible at this phase?
- Who decides, and who may mutate?
- When may simulation RNG be consumed?
- Which invariant is being protected?
- What are the relevant scale variables?
- What is the structural time and memory behavior, including memory lifetime?
- Is the code actually hot or merely theoretically interesting?
- Is the control flow readable and the change surface maintainable?
- Which focused tests prove the behavior?
- Can the existing frozen kernel already express the requirement?

If those questions become natural, you are no longer memorizing this codebase;
you are reasoning about it.