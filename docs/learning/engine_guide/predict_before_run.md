# Predict Before You Run

This page collects prediction prompts used throughout the guide. The habit is more
important than any single answer.

Before running or debugging code, write down what you expect.

## Transaction prediction

```text
Which object is authoritative?
Which object is working state?
If the next stage raises, which object survives?
Should committed RNG advance?
```

## Stage prediction

```text
What does process A see?
What does process B see?
Has any same-stage application happened yet?
What does the resolver receive?
What is materialized before application starts?
```

## RNG prediction

```text
Is this candidate already accepted?
Should this random decision occur for rejected candidates?
Which simulation-owned RNG is used?
What happens to its state if the transaction fails?
```

## Telemetry prediction

```text
Which event representation should be recorded?
Has the event committed?
Which effects should be attached?
What completed step index should telemetry carry?
```

## Complexity prediction

```text
What variables can grow?
What happens if each grows 10x?
Which delegated algorithm dominates?
What temporary memory grows?
What history persists?
```

## Code-review prediction

Before reading the implementation, infer from the contract:

```text
Which component should mutate?
Which should only choose?
Which dependencies should be explicit?
Which tests should exist?
```

Then compare the source with your model.

## Why prediction matters

Passive tracing tells you what happened.

Prediction plus tracing tells you **where your mental model is wrong**.

That mismatch is one of the fastest ways to improve architectural understanding.
