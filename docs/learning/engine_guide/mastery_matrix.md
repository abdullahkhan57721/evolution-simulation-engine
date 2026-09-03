# Mastery Matrix

Use this page to convert the textbook into a skill checklist. The goal is not to
check every box immediately; it is to see what "deep understanding" means.

## Levels

```text
1 Recognition
2 Explanation
3 Prediction
4 Diagnosis
5 Design
```

## Core concepts

| Concept | Recognition | Explanation | Prediction | Diagnosis | Design |
| --- | --- | --- | --- | --- | --- |
| transaction | identify working vs committed state | explain rollback/RNG isolation | predict failure outcome | spot direct-authoritative mutation | choose transaction boundary for new behavior |
| stage simultaneity | name propose→resolve→materialize→apply | explain common stage-start view | predict what proposers/materializers see | spot order-dependent science | decide whether behavior needs same or later stage |
| resolver/process split | identify chooser vs mutator | explain responsibility separation | predict accepted/apply sequence | spot resolver mutation | design conflict policy behind resolver contract |
| materialization | identify accepted-only phase | explain deferred stochastic work | predict RNG/work for rejected events | spot eager materialization | place new stochastic consequence correctly |
| state vs context | classify evolving/config values | explain copy vs shared-reference behavior | predict which value rolls back | spot hidden mutable config | design new dependency/state ownership |
| general propagation | identify source/recipient state transfer | explain why broader than inheritance | predict nonbiological use | spot biology-shaped generic API | design a new propagation specialization |
| biology specialization | map genome/inheritance/etc. | explain why biology stays above general layer | predict where new biology belongs | spot kernel biology leak | place new genetics/reproduction behavior |
| complexity | name scaling variables/classes | explain compositional cost | predict 10x scaling | spot misleading O(n) claim | select better algorithm/data structure |
| memory | identify persistent/temp/history memory | explain size + lifetime | predict retention growth | spot unbounded history/cache | design aggregation/streaming strategy |
| performance | distinguish profile/benchmark/Big-O | explain measurement-first rule | predict likely frequency hotspot | spot wrong-layer optimization | design evidence-backed optimization |
| readability | identify clear/unclear control flow | explain concrete criteria | predict cognitive impact of a refactor | spot fast-path explosion | choose clearer equivalent structure |
| maintainability | identify change radius/duplication | explain future-change cost | predict affected surfaces | spot duplicated policy | choose smallest stable public contract |

## Suggested checkpoints

### After Foundations

Target level 2–3 for:

```text
abstraction families
dependency design
state/configuration
complexity/performance basics
```

### After Kernel chapters

Target level 3–4 for:

```text
transactions
stages
materialization
resolver/process separation
ownership
```

### After Source Reading + Labs

Target level 4 for the kernel and level 3 for general evolution/biology mapping.

### After Capstones

Target level 5 for the major architecture concepts.

## How to use this matrix

If you can recognize an explanation but cannot predict behavior, do not reread the
whole textbook. Go to the focused chapter/test/lab for that concept and practice at
the next level.
