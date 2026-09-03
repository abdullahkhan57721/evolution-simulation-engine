# High-Value Contrast Reference

Many of the engine's hardest ideas become clearer when compared directly.

## State vs context

| State | Context |
| --- | --- |
| changes during execution | intended to remain immutable |
| transactionally copied | shared by reference |
| modeled facts | configuration/services/policies |
| may be rolled back | not part of step rollback |

## Resolver vs process

| Resolver | Process |
| --- | --- |
| chooses candidate transitions | proposes and applies owned transition type |
| conflict/ordering policy | domain transition mechanism |
| must not mutate domain state | owns domain mutation during apply |

## Proposal vs materialized event

| Proposal/resolved candidate | Materialized event |
| --- | --- |
| may still be rejected before materialization | accepted transition with deferred details determined |
| should avoid accepted-only expensive/random work | may safely consume accepted-only stochastic work |

## Propagation vs production

| Propagation | Production |
| --- | --- |
| constructs transmissible state | constructs an entity |
| can update an existing recipient | commonly creates a new entity |
| information-transfer question | entity-creation question |

## Expression vs realization

| Expression | Realization |
| --- | --- |
| maps transmissible state to expressed characteristics | combines expressed/transmitted information with environment/history/mutable state |
| biology: genetic architecture → genetic phenotype | biology: development/G×E/plasticity → realized phenotype |

## Selection vs fitness field

| Selection | Scalar fitness field |
| --- | --- |
| emergent differential future contribution | one possible summary/measurement |
| can be inferred from persistence/propagation outcomes | not required by general evolution contract |

## Participant vs investor vs genetic contributor vs production source

| Role | Meaning |
| --- | --- |
| participant | organism involved in reproductive episode/conflict |
| investor | proposal-time participant subset whose energy makes proposal affordable |
| genetic contributor | materialization-time subset whose genomes feed inheritance/pedigree parentage |
| production source | materialization-time subset supplied to offspring-production context |

Current simple policies may choose the same organisms for all four roles. The
concepts remain independent.

## Big-O vs profiling vs benchmarking

| Tool | Main question |
| --- | --- |
| complexity analysis | how does cost scale? |
| profiling | where did this run spend time? |
| benchmarking | how fast is a controlled workload/operation? |
| allocation profiling | where/when does memory allocation happen? |

## Ownership vs responsibility vs authority

| Concept | Question |
| --- | --- |
| ownership | who contains/retains this state/object? |
| responsibility | which problem is this component supposed to solve? |
| authority | which decision/mutation is it allowed to make? |

`Simulation` owns authoritative state. A resolver has authority to select
transitions. A process has authority to mutate its owned domain transition during
application.

## Abstract vs generic vs concrete

| Term | Meaning here |
| --- | --- |
| abstract | concept stripped to relevant common structure |
| generic | implementation/contract usable across concrete types/domains |
| concrete | specific realized model/type/policy |

A generic implementation can realize an abstraction, but the words are not
synonyms.

## Readability vs maintainability

| Readability | Maintainability |
| --- | --- |
| cost to understand code now | cost/risk to change code later |
| local control flow/naming/cognitive load | duplication/change radius/tests/coupling/parallel paths |

They often reinforce each other, but not always.

## Architecturally important vs hot

| Architecturally important | Hot path |
| --- | --- |
| meaning/risk to system design | measured/frequent runtime contribution |
| can run once | often runs repeatedly |
| e.g. compilation contract | e.g. per-event telemetry construction in measured kernel workload |

Do not optimize based on architectural importance or visual complexity alone.
