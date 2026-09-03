# Quality Tradeoff Mini-Examples

## Readable and fast

Cache stable dispatch metadata once. Removes repeated work and simplifies the hot
path.

## Fast but harder to maintain

Duplicate the stage algorithm into several special-case loops. May save branches
but multiplies invariant paths.

## Extensible but overengineered

Create multiple factories/registries for one implementation with no demonstrated
variation point.

## Simple but incorrectly coupled

Put genome-specific fields on generic `SimulationState`. Locally convenient, but
breaks domain neutrality.

## Memory efficient but less observable

Discard all event history. Lower retention, but potentially unacceptable for
scientific causality/debugging. Consider summaries/streaming instead of assuming
one axis wins.
