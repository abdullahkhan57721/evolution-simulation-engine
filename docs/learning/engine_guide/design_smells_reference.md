# Architecture Smells and Healthy Counterpatterns

Use this as a review aid, not a rulebook. A smell is a reason to investigate, not
a proof that code is wrong.

| Smell | Typical symptom | Healthier direction |
| --- | --- | --- |
| biology leak | kernel API names organisms/genomes/energy/mating | keep meaning in biological/domain layer |
| god process | one process proposes, resolves, mutates, observes, and configures | split real responsibilities across process/resolver/policies/observation |
| hidden dependency | globals/service locators/independent RNGs | explicit state/context/dependency injection |
| order-dependent science | same-stage result changes because process order changes | stage simultaneity or explicit later stage |
| duplicated policy | same rule appears in several packages | one owning policy/contract |
| boolean explosion | generic code accumulates flags for domain variants | composition or a real policy abstraction |
| premature generalization | contract exists only for imagined futures | wait for demonstrated variation/pressure |
| fast-path explosion | parallel algorithms differ only for tiny constant savings | one semantic path plus measured stable optimizations |
| observer as repair mechanism | invalid state is fixed after commit | enforce correctness before/at application |
| resolver mutation | conflict policy directly changes domain state | resolver selects, process applies |
| hidden stochasticity | component creates its own simulation RNG | use transaction-owned RNG at correct phase |
| telemetry-as-state | causal records become authority for modeled facts | state owns modeled truth; telemetry describes commits |

## Questions before refactoring a smell

```text
Is the behavior actually incorrect or merely unfamiliar?
Which invariant/contract defines the intended boundary?
Is there a focused test that proves the current semantics?
Would the proposed abstraction reduce or increase concepts?
Is the problem local or public-contract-wide?
Is performance evidence involved, or only speculation?
```

## Positive patterns to recognize

```text
small capability contract
explicit composition
policy object for a real axis of variation
immutable configuration
transactional modeled state
accepted-only materialization
resolver/process separation
focused invariant tests
measurement-first optimization
one readable orchestration path
```

The goal is not to maximize the number of patterns. It is to make ownership,
variation, and invariants explicit with the smallest useful structure.
