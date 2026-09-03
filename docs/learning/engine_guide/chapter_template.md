# Chapter Design Template

This page is primarily for future textbook maintenance. Major chapters should
follow a recognizable pedagogical rhythm without becoming mechanically identical.

## Recommended rhythm

```text
1. Where you are in the architecture
2. Why this topic matters
3. Mental model
4. Naive/simple design
5. Failure mode
6. Abstraction / contract
7. Contrast or misconception check
8. Simplified pseudocode
9. Real repository implementation
10. Focused tests / invariants
11. Engineering analysis
12. Predict-before-running question
13. Mastery criteria
14. Where to go next
```

## Engineering analysis block

For important implementation chapters include, when relevant:

```text
correctness / semantics
scaling variables
time complexity
delegated costs
memory size + lifetime
execution frequency
measured performance evidence
readability
maintainability / change radius
extensibility
testability
optimization boundary
```

Do not force complexity sections onto purely conceptual material where they add no
value.

## Contrast block

Use side-by-side contrasts for concepts readers commonly conflate.

Examples:

```text
state vs context
resolver vs process
propagation vs production
proposal vs materialized event
Big-O vs profiling
readability vs maintainability
```

## Misconception block

Prefer plausible mistakes over strawmen.

Show code a competent engineer could reasonably write, then identify which
responsibility/invariant it violates.

## Mastery block

Use design-level prompts:

```text
You understand this chapter if you can...
```

Avoid trivia-heavy factual recall.

## Scaffolding rule

Early chapters:

```text
more diagrams
more annotations
more worked answers
```

Later chapters:

```text
more questions
blank worksheets
review tasks
capstones
```

This fading is intentional.

## Maintenance rule

If a stable architecture concept changes, update the authoritative contract first
or in the same milestone. Then revise the pedagogical explanation. Do not make the
textbook the source of truth for public semantics.
