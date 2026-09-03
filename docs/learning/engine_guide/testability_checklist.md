# Testability Checklist

```text
[ ] Can the key invariant be expressed in one focused test?
[ ] Can collaborators be replaced with small fakes/stubs?
[ ] Is mutation localized enough to assert precisely?
[ ] Are deterministic seeds/RNG semantics controllable?
[ ] Does failure leave authoritative state inspectable?
[ ] Can resolver policy be tested without full domain runtime?
[ ] Can domain policy be tested without changing kernel orchestration?
[ ] Does a failing test point toward one responsibility?
```

Difficulty isolating a behavior can signal excessive coupling or collapsed
responsibilities.
