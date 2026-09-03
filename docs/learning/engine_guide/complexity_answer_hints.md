# Complexity Exercise Hints

Use these only after attempting the exercises.

## Proposal aggregation

Visiting `P` processes and collecting `Q` event references is O(P + Q) kernel-side
work with O(Q) proposal-list storage, excluding each process's proposal algorithm.

## Opaque domain copy

The kernel must keep `C_domain_copy(N)` / `M_domain_copy(N)` explicit because the
payload representation is domain-defined.

## Dispatch

Repeated linear search is O(RP). Average constant-time dictionary dispatch reduces
the repeated lookup portion to O(R) while spending O(P) stable dispatch metadata.

## Resolver

Returning/copying the proposal sequence is linear. Sorting is O(Q log Q). A generic
stage cannot claim one resolver complexity.

## Accepted-only materialization

The number of expensive materializations can scale with `R` instead of `Q`, but the
primary reason is preserving accepted-only semantics/RNG timing.

## Constant-time hotspot

Need invocation frequency, constant cost, allocations, and profile evidence.

## Observer retention

Full O(N) snapshots across T roughly stable steps imply O(TN) retained history.

## Wrong-layer optimization

Profile/domain evidence points first to spatial/genetics/observation. An uncached
O(K) startup/configuration-looking operation is not automatically a runtime target.

## All-pairs scaling

A 10x increase in N makes O(N^2) pair work roughly 100x. Investigate spatial
indexing/neighborhood restriction or other scientifically equivalent domain
algorithms before kernel changes.

## Benchmark validity

Different stochastic work invalidates a simple speed conclusion. Control seed,
configuration, environment where practical, and outcome/work dimensions.
