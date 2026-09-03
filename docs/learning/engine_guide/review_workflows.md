# Review Workflows and Worksheets

This page turns the textbook into a reusable workflow for source reading, feature
design, PR review, debugging, and performance work.

The goal is not to fill every blank mechanically. The worksheets force you to ask
which questions matter before implementation details dominate your attention.

# Reading an unfamiliar file

Use this order:

```text
1. Identify the architectural layer.
2. Read the public contract/docstring.
3. Find focused tests.
4. State the invariant in your own words.
5. Locate top-level control flow.
6. Separate essential semantics from support/optimization plumbing.
7. Mark inputs, outputs, mutation, ownership, and decision authority.
8. Define relevant scale variables.
9. Estimate structural time and memory lifetime.
10. Only then inspect low-level helpers and optimizations.
```

This is usually more effective than reading from line 1 to EOF.

## Source-review worksheet

```text
File / component:
________________________________________

Architectural layer:
________________________________________

Question this component answers:
________________________________________

Public responsibility:
________________________________________

Inputs:
________________________________________

Outputs:
________________________________________

What does it read?
________________________________________

What may it mutate?
________________________________________

What decisions/authority does it own?
________________________________________

Core algorithm in one sentence:
________________________________________

Invariant(s):
________________________________________

Focused tests:
________________________________________

Essential semantics:
________________________________________

Support / diagnostics / optimization plumbing:
________________________________________

Scale variables:
________________________________________

Structural time:
________________________________________

Delegated/unknown costs:
________________________________________

Memory growth + lifetime:
________________________________________

Execution frequency:
________________________________________

Measured-hot evidence, if any:
________________________________________

Readability strengths/risks:
________________________________________

Maintainability/change radius:
________________________________________

Extensibility axis:
________________________________________

What would be dangerous to simplify?
________________________________________
```

# Reviewing a PR

Before approving a consequential change, answer:

```text
What problem is being solved?
Which layer owns it?
What public contract changes?
What stable invariant could regress?
What tests prove new/unchanged semantics?
Does state visibility change?
Does RNG timing/ownership change?
Does mutation authority move?
What are realistic scaling variables?
What allocation/retention changes?
Is measured performance evidence needed?
Does top-level control flow remain readable?
Does the change create duplicate semantic paths?
Could the same goal fit an existing contract?
Are authoritative docs/ADRs updated if necessary?
```

## PR review worksheet

```text
Issue / PR:
________________________________________

Intended behavior:
________________________________________

Owning layer:
________________________________________

Public API impact:
________________________________________

Invariant impact:
________________________________________

State/RNG/ordering impact:
________________________________________

Tests added/updated:
________________________________________

Complexity impact:
________________________________________

Memory/lifetime impact:
________________________________________

Performance evidence required/provided:
________________________________________

Readability:
________________________________________

Maintainability/change radius:
________________________________________

Extensibility:
________________________________________

Documentation impact:
________________________________________

Approve / request change / follow-up and why:
________________________________________
```

# Designing a new feature

Use architecture from the outside in.

```text
domain/scientific requirement
        |
        v
identify owning layer
        |
        v
try existing contracts
        |
        v
locate exact gap, if any
        |
        v
state gap without domain-specific wording
        |
        v
change lower layer only if the generic deficiency remains real
```

## Feature architecture worksheet

```text
Feature / modeled behavior:
________________________________________

Scientific/domain meaning:
________________________________________

Owning layer:
________________________________________

Mutable modeled state required:
________________________________________

Immutable configuration/services required:
________________________________________

Candidate transition(s):
________________________________________

Potential conflicts:
________________________________________

When should randomness be consumed and why?
________________________________________

Does accepted-only materialization help?
________________________________________

Who owns application/mutation?
________________________________________

Telemetry/observation required:
________________________________________

Expected scale variables:
________________________________________

Expected time complexity:
________________________________________

Memory size/lifetime considerations:
________________________________________

Likely hot path or only theoretical scaling risk?
________________________________________

Focused invariants/tests:
________________________________________

Can existing contracts express it?
________________________________________

If not, state the generic deficiency without domain vocabulary:
________________________________________
```

The last question is especially important before changing the frozen kernel.

# Performance review workflow

```text
observe/reproduce performance problem
        |
        v
identify the correct layer
        |
        v
profile representative workload
        |
        v
inspect algorithm/data structures first
        |
        v
inspect repeated work/allocation second
        |
        v
propose smallest clear change
        |
        v
run focused semantic tests
        |
        v
benchmark comparable before/after
        |
        v
weigh measured value against readability/maintenance cost
```

## Performance review worksheet

```text
Workload/scenario:
________________________________________

Correct layer being measured:
________________________________________

Reproducibility controls (seed/config/outcomes/environment):
________________________________________

Dominant profile path(s):
________________________________________

Scale variables:
________________________________________

Current algorithmic complexity:
________________________________________

Current memory/lifetime behavior:
________________________________________

Per-operation frequency:
________________________________________

Measured bottleneck or speculative concern?
________________________________________

Candidate algorithm/data-structure improvement:
________________________________________

Candidate constant-factor/allocation improvement:
________________________________________

Optimization risk class:
structurally safe / semantics-sensitive / architecture-changing

Semantics tests protecting the change:
________________________________________

Comparable before/after evidence:
________________________________________

Readability cost:
________________________________________

Maintainability cost:
________________________________________

Decision:
________________________________________
```

Remember that an O(1) operation can be hot because frequency and constant cost
matter. Conversely, a complicated preflight traversal can be irrelevant to run
time because it executes once.

# Debugging workflow

Before stepping through code, predict:

```text
current authoritative/working state identity
step index
stage index
current phase
what state the code should observe
whether RNG should have advanced
whether domain mutation should have happened
whether telemetry should exist yet
```

At the breakpoint compare reality with the prediction. The mismatch is often more
informative than passively watching values change.

## Debugging worksheet

```text
Breakpoint:
________________________________________

Expected phase:
________________________________________

Expected state identity (authoritative/working):
________________________________________

Expected domain value(s):
________________________________________

Expected RNG state/draw count:
________________________________________

Expected event status (proposal/resolved/materialized/applied):
________________________________________

Expected telemetry:
________________________________________

Observed difference:
________________________________________

Which invariant/mental model explains the mismatch?
________________________________________
```

# Refactoring and maintainability review

For a proposed refactor ask:

```text
Which concepts disappear?
Which concepts are added?
How many semantic paths exist before and after?
How wide is the change radius?
Are dependencies more explicit or more hidden?
Are tests easier to localize?
Is the top-level algorithm easier to see?
Does a private optimization leak into public architecture?
```

A refactor that reduces line count but creates more hidden invariants can be a net
loss.

# Architecture smells to scan for

Use [Architecture Smells and Healthy Counterpatterns](design_smells_reference.md)
as a prompt, especially for:

```text
biology leakage into generic kernel
resolver mutation
observer-as-repair
hidden simulation RNGs
order-dependent science
speculative generalization
boolean/special-case explosion
performance fast-path explosion
```

A smell is evidence to investigate, not automatic proof of bad code.

# A compact multi-lens Engineering Review Card

For important functions/components, summarize:

| Lens | Question |
| --- | --- |
| Responsibility | What problem does it own? |
| Semantics | What must remain true? |
| Time | How does structural work scale? |
| Memory | What is allocated/retained and for how long? |
| Frequency | How often does it execute? |
| Performance | Is it measured hot? |
| Readability | Can the semantic algorithm be seen? |
| Maintainability | How many paths/rules must stay aligned? |
| Extensibility | What real behavior can vary independently? |
| Testability | Which focused tests prove its guarantees? |
| Boundary | What tempting shortcut should be rejected? |

The [Engineering Anatomy of the Kernel](kernel_engineering_anatomy.md) demonstrates
this card on the actual kernel.

# Review capability ladder

Use the worksheets less as you gain fluency.

```text
RECOGNIZE
    identify the pieces

EXPLAIN
    state why they exist

PREDICT
    predict behavior and cost

DIAGNOSE
    identify invariant/boundary violations

DESIGN
    independently choose the correct architecture and evidence
```

The goal is not permanent dependence on checklists. The goal is for these
questions to become automatic.

## Next

Use this page while attempting the [Capstone Challenges](capstones.md).