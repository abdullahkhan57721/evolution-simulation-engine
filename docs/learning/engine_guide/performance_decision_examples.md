# Performance Decision Mini-Examples

## Optimize

Profile shows a repeated O(P) process scan for every accepted event; stage process
set is stable. Replacing it with a construction-time dictionary reduces repeated
work, preserves semantics, and keeps control flow clear.

## Measure first

A new O(N^2) mating algorithm is expected to run on small populations today but may
scale later. Record the hazard and benchmark/profile representative target scales
before building a complex index.

## Reject

A 0.5% microbenchmark gain requires materializing rejected events before resolution.
This changes RNG/work semantics; reject regardless of the local speedup unless the
public stage contract itself is intentionally reconsidered.

## Stop

The remaining kernel overhead is 3% of end-to-end runtime, no structural hotspot
is visible, and proposed savings require duplicated stage algorithms. Move
performance work to the dominant domain layer or stop.
