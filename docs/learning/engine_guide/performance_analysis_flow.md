# Performance Analysis Flow

```text
MODELED QUESTION
What scale matters scientifically?
        |
        v
COMPLEXITY
How should cost grow?
        |
        v
WORKLOAD
Can we reproduce representative execution?
        |
        v
PROFILE
Which layer/path actually dominates?
        |
        v
DESIGN
Algorithm/data structure/repeated work/allocation?
        |
        v
SEMANTIC REVIEW
Ordering, RNG, state visibility, contracts preserved?
        |
        v
QUALITY REVIEW
Readable? maintainable? testable?
        |
        v
MEASURE
Comparable before/after benchmark + focused tests
        |
        v
DECIDE
Benefit worth total engineering cost?
```
