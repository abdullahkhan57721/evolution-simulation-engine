# Questions to Ask While Reading Code

Keep these questions beside your editor.

## Meaning

```text
What problem is this code solving?
Which layer owns that problem?
What does the code intentionally not know?
```

## State and authority

```text
What does it read?
What can it mutate?
Who owns the authoritative object?
Who chooses versus who applies?
```

## Runtime semantics

```text
Which phase am I in?
What state snapshot is visible?
When can randomness be consumed?
What constitutes commit?
```

## Computation

```text
What variables can grow?
What is local structural work?
What delegated calls may dominate?
What does memory allocate/retain and for how long?
How often does this execute?
```

## Quality

```text
Can I see the core control flow?
Are dependencies explicit?
Is one rule duplicated?
How wide is the change radius?
What real behavior varies behind this abstraction?
```

## Evidence

```text
Which test states the invariant?
Which ADR/doc explains the rationale?
Is this actually a measured hotspot?
What benchmark/profile would answer the unresolved question?
```

If you can answer these, syntax is rarely the hard part anymore.
