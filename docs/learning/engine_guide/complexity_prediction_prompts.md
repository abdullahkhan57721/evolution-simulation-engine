# Complexity Prediction Prompts

Before profiling or running a larger scenario, predict:

```text
Which quantity is growing?
Which loops depend on it?
Which data structures are created per item?
Which callbacks hide additional work?
What is temporary versus retained?
Which operation repeats at the highest frequency?
What should happen at 10x scale?
Which layer do I expect to dominate?
```

Then compare the profile with your prediction. A wrong prediction is useful: it
reveals where your computational mental model needs correction.
