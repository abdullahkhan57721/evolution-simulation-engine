# Source Walkthrough Engineering Sidebar

When the main source walkthrough points here, add this compact analysis beside the
file you are reading:

```text
SEMANTICS
What must remain true?

COMPLEXITY
What local variables scale, and what delegated work remains unknown?

MEMORY
What is copied/allocated/retained and for how long?

FREQUENCY
How often is this path invoked?

EVIDENCE
Is it actually measured hot?

READABILITY
Can you see the algorithm without understanding every helper?

MAINTAINABILITY
How many semantic paths/change surfaces exist?

OPTIMIZATION BOUNDARY
Which shortcut would damage the contract or create disproportionate complexity?
```

For full cards use [Engineering Anatomy of the Kernel](kernel_engineering_anatomy.md).
