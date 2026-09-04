# B3 Flagship Cinematic

The B3 flagship cinematic is the explanatory Manim presentation for the confirmed
environment-dependent `max_speed` experiment. It is a downstream presentation
consumer, not a second simulation or experiment-analysis path.

The scientific source of truth is
[`flagship_evolution_demo.md`](flagship_evolution_demo.md). The cinematic must not
reinterpret discovery results, choose a different representative seed, or infer
biological events from visual proximity or organism identity continuity.

## Scientific and presentation boundary

The concrete data flow is:

```text
frozen B3 specification
        ↓
completed B3 committed evidence
        ↓
B3 scientific handoff
        ↓
B3FlagshipDirectorPlan
        ↓
B3-specific Manim choreography
        ↓
video + reproducibility manifest
```

`B3FlagshipDirectorPlan` is intentionally specific to this confirmed scenario. It
is not a generic camera language, film DSL, scene graph, or scenario-presentation
schema.

The director preserves the scientific visual grammar:

- organism position comes from committed spatial observations;
- organism fill encodes committed genetic-phenotype `max_speed` on one fixed
  `1..4` scale;
- organism size continues to represent authoritative body mass;
- focus uses outline/halo/camera framing rather than changing fill or size;
- resource glyphs come from committed resource deposits;
- feeding, reproduction, birth, death, or other causal claims require committed
  event evidence;
- appearance/departure remains non-causal identity continuity metadata;
- only organism position may be visually interpolated between exact committed
  endpoints;
- matched treatment/control worlds and genetic charts use common scientific
  scales.

## Representative evidence

The cinematic uses B3's predeclared representative seed `5`. Its two directed
mechanism examples are the exact authoritative compact-treatment episodes selected
by the B3 handoff:

- organism `16`, `max_speed = 1`, completed step `7`;
- organism `1`, `max_speed = 4`, completed step `5`.

They are separate examples from the same representative run, not a head-to-head
contest and not experimental replicates. Full robustness evidence comes from the
eight independent B3 confirmation seeds.

## Install the optional renderer

```bash
venv/bin/python -m pip install -r requirements-animation.txt
```

Manim remains isolated from the ordinary engine and cinematic-preparation import
path.

## Render the reduced director excerpt

Routine CI exercises a reduced deterministic excerpt through the real B3 director
without rerunning the full confirmation/sensitivity set:

```bash
venv/bin/python examples/render_b3_flagship_cinematic.py \
  --excerpt \
  --quality low \
  --output outputs/b3-director-smoke.mp4
```

The excerpt still reruns the frozen representative control/treatment seed and
validates the declared representative episodes against committed evidence.

## Render the full flagship

The default command reproduces the representative matched pair, the complete
independent confirmation set, and the radius-2 sensitivity set before directing the
full film:

```bash
venv/bin/python examples/render_b3_flagship_cinematic.py \
  --quality high \
  --output outputs/b3-flagship-cinematic.mp4
```

The output is accompanied by
`outputs/b3-flagship-cinematic.manifest.json`. The manifest records stable scenario,
seed, selected episode, focal-scale, confirmation, director, renderer, and quality
identifiers without local absolute paths or live simulation objects.

## Deliberate full-artifact CI verification

The full 1080p/60-fps flagship is deliberately **not** part of routine pull-request
CI. The existing cinematic workflow always runs the generic, science-aware, and
reduced B3 smokes. For the V3 I2 candidate PR, add this exact marker to the PR body:

```text
FULL_B3_CINEMATIC=1
```

That marker enables the `Full high-quality B3 flagship artifact` job on the current
PR head. If rendered output is corrected afterward, every subsequent synchronized
head reruns the full job while the marker remains present. This makes the inspected
video and the reviewed code head identical without imposing the full render cost on
ordinary development.

The full job validates the video stream, `1920x1080` output, representative seed,
committed step range, fixed `max_speed` scale, all eight confirmation seeds, radius-2
sensitivity inclusion, and the reproducibility manifest before uploading the video
and manifest as a GitHub Actions artifact.

## Narrative structure

The concrete director follows the B3 renderer-neutral storyboard:

```text
QUESTION
  ↓
ENVIRONMENTAL DIFFERENCE
  ↓
INDIVIDUAL CONSEQUENCE
  ↓
REPEATED INTERACTIONS
  ↓
DIFFERENTIAL REPRODUCTIVE CONTRIBUTION
  ↓
POPULATION CHANGE
  ↓
EVOLUTIONARY EVIDENCE + ROBUSTNESS
  ↓
BOUNDED CONCLUSION
```

Simulation time and cinematic time are intentionally different. Cuts and holds may
compress the explanation, but committed snapshots are labeled as such, skipped
steps are not presented as interpolated scientific states, and the director never
changes B3 parameters to improve visual pacing.

## Claim boundary

The final film supports the bounded B3 result: within the tested reference ecology,
changing only renewable-resource geography changes the evolutionary fate of
standing heritable `max_speed` variation; compact radius-1 patches favor the
high-speed strategy relative to matched uniform controls, while the uniform
environment favors the lower-speed strategy in aggregate.

It does not establish a universal optimal speed, a generic effect of all patchy
environments, isolated locomotion-cost causality, or empirical species calibration.
