# Final Textbook Blueprint

The textbook is organized into five conceptual phases.

## Part I — Think Like a Software Engineer

```text
How to use the textbook
Software Architecture Primer
Architecture Quality
Computational Complexity & Performance Thinking
Memory Analysis / tradeoff references
```

## Part II — Think Like a Simulation Designer

```text
Simulation Fundamentals
transactions
stages
conflicts
randomness
observation
```

## Part III — Think Like an Evolution Modeler

```text
General Evolution
Biological Specialization
worked layer comparisons
```

## Part IV — Understand This Engine

```text
Kernel Mental Model
Kernel Public API
Kernel Runtime
Design Rationale & Invariants
Architecture History
Engineering Anatomy
Performance Case Studies
Source Walkthrough
```

## Part V — Prove You Understand It

```text
Debugger Labs
Prediction exercises
Complexity exercises
Reasoning About Proposed Changes
Code/PR review workflows
Architecture worksheets
Mini-kernel exercise
Capstones
Cheat sheets / mastery matrix
```

## Final success criterion

A reader succeeds when they can open unfamiliar kernel code, identify its layer
and responsibility, explain the architectural reason it exists, trace its runtime
data flow, identify its invariants, reason about time and memory behavior,
distinguish theoretical complexity from measured performance, evaluate
readability/maintainability/extensibility/testability, find the focused tests that
protect it, and judge whether a proposed change belongs there.

No further topic expansion should occur unless a real learning gap appears during
use of the textbook.
