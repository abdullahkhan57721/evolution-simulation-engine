# Extensibility Checklist

```text
[ ] What concrete behavior needs to vary?
[ ] Can it vary behind an existing contract?
[ ] Is the abstraction domain-neutral at its intended layer?
[ ] Does the new extension point preserve stronger domain vocabulary above?
[ ] Is there at least one real use/pressure for the abstraction?
[ ] Does it avoid pushing future hypothetical details into lower layers?
[ ] Can a new implementation be tested independently?
```

Extensibility means supporting real axes of change cleanly, not predicting every
future requirement.
