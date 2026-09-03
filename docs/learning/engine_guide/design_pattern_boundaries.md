# Useful Patterns Without Pattern Collecting

The textbook uses several recurring software-design forms. Learn the problem each
solves rather than memorizing a catalog.

## Policy object

Use when a real decision rule must vary independently.

Examples:

```text
resolver policy
inheritance policy
variation policy
stopping condition
```

## Adapter

Use when one domain concept must satisfy/translate to a broader contract without
moving the domain's meaning downward.

## Capability contract

Use when callers need one narrow behavior rather than membership in a large
inheritance hierarchy.

## Composition root

Use a high-level place to assemble concrete policies/components while keeping
lower layers independent of that assembly.

## Transaction

Use when a sequence of mutations must either commit together or leave authoritative
state unchanged.

## Observer

Use when committed outcomes need to be measured without participating in the
transition decision itself.

## Resolver

Use when candidate transitions can conflict and selection must remain separate
from mutation.

## Stop before pattern explosion

Do not add:

```text
factory
registry
provider
adapter
strategy
builder
```

merely because the names sound architectural. Every abstraction adds a concept a
future reader must learn.

Ask:

> What concrete variation or responsibility separation does this pattern buy us?

If the answer is unclear, a function or direct composition may be better.
