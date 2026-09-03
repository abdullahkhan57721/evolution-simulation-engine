# Performance Scope Boundary

The textbook teaches performance judgment through this engine. It does not attempt
to teach every layer of computer performance.

Deep dives into CPU caches, branch prediction, compiler optimization, SIMD, custom
allocators, or native extensions should be added only when a measured engine
problem makes them relevant.

The default progression remains:

```text
complexity
-> representative profile
-> algorithm/data structure
-> repeated work/allocation
-> focused benchmark
-> lower-level techniques only if still justified
```
