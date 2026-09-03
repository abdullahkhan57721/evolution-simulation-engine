# Engineering Analysis Index

Use this page when you want to study the kernel as production software rather than
only as an execution model.

## Learn the analytical tools

1. [Architecture Quality](architecture_quality.md)
2. [Computational Complexity and Performance Thinking](computational_complexity.md)
3. [Memory Analysis for Simulations](memory_analysis.md)
4. [Performance, Readability, and Maintainability Together](performance_readability_maintainability.md)

## Apply them to the kernel

1. [Engineering Anatomy of the Kernel](kernel_engineering_anatomy.md)
2. [Performance Case Studies](performance_case_studies.md)
3. [Scaling Thought Experiments](scaling_thought_experiments.md)
4. [Source Analysis Method](source_analysis_method.md)

## Use while reading/reviewing

- [Engineering Review Cards](engineering_review_cards.md)
- [High-Value Contrast Reference](contrast_reference.md)
- [Architecture Smells and Healthy Counterpatterns](design_smells_reference.md)
- [Review Workflows](review_workflows.md)
- [Complexity Quick Reference](complexity_quick_reference.md)

## Practice

- [Complexity and Performance Exercises](complexity_exercises.md)
- [Reasoning About Proposed Changes](change_reasoning.md)
- [Mastery Matrix](mastery_matrix.md)
- [Capstone Challenges](capstones.md)

## The central review question

For any important code, aim to answer:

```text
What problem does it own?
What invariant does it protect?
What is the algorithm?
How does cost scale?
What memory is allocated and for how long?
How frequently does it execute?
What is actually measured hot?
Can a human understand the control flow?
How risky is future change?
What can vary behind existing contracts?
Which tests prove the semantics?
```
