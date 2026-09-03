# Hot-Path Checklist

Before calling code "hot":

```text
[ ] Representative workload defined?
[ ] Correct architectural layer isolated?
[ ] Invocation frequency known?
[ ] Profile shows material cumulative/self time?
[ ] Scale variables identified?
[ ] Allocation behavior relevant?
[ ] Dominant delegated function separated from caller overhead?
[ ] Before/after measurement plan exists?
```

Code that merely sits inside a loop is not automatically the dominant hotspot.
