# Readability Checklist

Use concrete criteria.

```text
[ ] Core algorithm visible in one place?
[ ] Names expose domain/architectural meaning?
[ ] Important dependencies explicit?
[ ] Mutation sites obvious?
[ ] Branch/special-case count reasonable?
[ ] Helpers correspond to meaningful concepts?
[ ] Performance plumbing separated from semantic flow?
[ ] Cause and effect remain close enough to understand?
[ ] Comments explain why, not restate syntax?
[ ] A new reader can identify what to ignore on first pass?
```

Readability is not merely short code. A few explicit lines can be clearer than a
compressed expression that hides phase boundaries.
