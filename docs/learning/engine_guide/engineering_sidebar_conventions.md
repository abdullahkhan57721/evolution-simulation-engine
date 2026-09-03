# Engineering Sidebar Conventions

To keep the textbook scannable, engineering notes should use a few recurring
labels rather than long prose every time.

## Complexity

```text
**Complexity.** Define local variables, state structural time/space, then name
excluded delegated costs.
```

## Memory

```text
**Memory.** State both growth and lifetime (stage, step, run, retained history).
```

## Hot path

```text
**Hot-path status.** Distinguish frequency/theoretical hazard from measured profile evidence.
```

## Readability

```text
**Readability.** Note control-flow locality, naming, branching, hidden dependencies, cognitive load.
```

## Maintainability

```text
**Maintainability.** Note duplicated semantics, number of code paths, change radius, and test localization.
```

## Optimization boundary

```text
**Optimization boundary.** State the tempting shortcut and which semantic or maintenance guarantee constrains it.
```

Use these only where they add insight. Do not annotate every trivial operation.
