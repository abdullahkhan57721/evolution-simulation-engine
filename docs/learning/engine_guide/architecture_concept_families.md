# Architecture Concept Families

Use these families instead of memorizing a flat glossary of unrelated terms.

## Modeling abstractions

```text
abstraction
contract / interface
implementation
generalization
specialization
generic vs concrete
```

Question:

> What common structure matters, and what detail belongs in a specialization?

## Dependency design

```text
dependency
dependency direction
dependency injection
dependency inversion
composition root
```

Question:

> Who is allowed to know about whom, and how are concrete dependencies supplied?

## Responsibility design

```text
separation of concerns
cohesion
coupling
orchestration
policy
adapter
capability
```

Question:

> Which component owns each decision or behavior, and what should vary independently?

## State and execution

```text
state
configuration/context
mutation
side effect
transaction
commit / rollback
determinism
observation / telemetry
```

Question:

> What changes, what remains stable, and when does an effect become authoritative?

## Performance analysis

```text
scaling variables
Big-O / Theta
auxiliary space
memory lifetime
frequency
hot path
profiling
benchmarking
allocation measurement
time-space tradeoff
```

Question:

> How does cost grow, what is actually expensive, and what tradeoff is justified?

Organizing vocabulary this way helps the terms form a connected mental model.
