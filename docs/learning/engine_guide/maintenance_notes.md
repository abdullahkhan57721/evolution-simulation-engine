# Textbook Maintenance Notes

The textbook is deliberately more redundant than authoritative documentation
because repetition, contrasts, and worked examples help learning. That creates a
staleness risk. Use these rules when maintaining it.

## Source-of-truth rule

When the guide disagrees with current code/tests or authoritative architecture
docs, the guide is wrong.

Update authoritative contracts first or in the same milestone, then update the
pedagogical explanation.

## Stable concepts versus volatile details

Prefer teaching:

```text
public semantic contracts
ownership
layer boundaries
invariants
stable examples
reasoning methods
```

Avoid embedding:

```text
current CI status
volatile SHAs
transient issue progress
machine-specific timing as permanent truth
```

Historical timing may appear only as labeled case-study evidence.

## Prevent duplication drift

When several pages need the same exact rule, choose one deeper explanation and
cross-link from references/cheat sheets.

Spiral learning should add depth:

```text
concept -> source -> engineering tradeoff -> practice
```

not copy the same paragraph four times.

## Review after architecture changes

Search the textbook for affected vocabulary and inspect:

```text
landing-page diagrams
contrast reference
source walkthrough
engineering review cards
worked examples
exercises/capstones
glossary/cheat sheets
```

## Review after performance changes

Ask whether the change affects:

```text
algorithmic complexity
memory behavior
measured-hot case studies
optimization boundaries
source-reading advice
```

Do not update historical examples to pretend they were always different; label
history clearly or replace it with a more stable lesson.

## Keep the book finite

Before adding a new chapter ask:

```text
Does it help understand this engine?
Does it teach a transferable skill through this engine?
Is the concept important enough for a chapter rather than a link/sidebar?
Can it be consolidated with an existing family?
```

Do not turn this resource into a full Python, algorithms, design-patterns, or CPU
performance textbook.
