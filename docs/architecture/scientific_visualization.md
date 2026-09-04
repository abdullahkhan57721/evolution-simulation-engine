# Scientific Visualization Architecture

Evolution Simulation Engine treats visualization as a downstream scientific
presentation concern. Renderers may improve clarity, interaction, pacing, and
visual polish, but they do not redefine simulation truth.

The governing principle is:

> Generalize the visual vocabulary, not the scientific meaning.

## Three-layer responsibility model

Scientific visualization has three distinct responsibilities:

```text
committed scientific evidence
        |
        v
scenario-specific scientific encoding
        |
        +-------------------------+
        |                         |
        v                         v
interactive renderer       cinematic renderer
        |                         |
        v                         v
renderer primitives        renderer primitives
        |                         |
        v                         v
interactive choreography   cinematic choreography
```

### Layer 1 — visual primitives

A renderer owns the concrete primitives it can express: world surfaces,
organisms, resources, environmental context, carcasses, trails, selection,
event overlays, connectors, annotations, legends, statistic cards, charts,
timelines, and comparisons.

This is a shared **conceptual vocabulary**, not a universal runtime scene graph.
An interactive browser renderer and an offline cinematic renderer may implement
an organism with completely different technologies. No shared lower-level object
model is required merely because both can display organisms.

Layer 1 answers:

> What can this renderer express?

It does not decide that `max_speed`, age, mating type, defense, or any other
particular variable is always scientifically important.

### Layer 2 — scientific encoding

Scenario-specific scientific encoding maps authoritative evidence onto visual
channels. It determines which variables are focal, what organism color or another
channel means, which environmental context matters, which events deserve emphasis,
which statistics are primary, and which treatment/control comparisons must remain
semantically matched.

Layer 2 answers:

> What does the visual grammar mean for this experiment?

Scientific encoding remains renderer-neutral. It must not contain Plotly traces,
CSS, JavaScript objects, Manim animations, Blender materials, camera timing,
easing curves, or other implementation-specific presentation objects.

The responsibility is architecturally real, but the repository should not create
a broad `ScenarioPresentationSpec` before multiple concrete scenarios establish
the fields that genuinely repeat. Small immutable shared presentation values may
be introduced when real consumers demonstrate a stable shared need.

### Layer 3 — choreography

Each medium independently organizes attention.

An interactive application may guide users through configuration, a world-centered
workspace, timeline inspection, selected-organism details, analytics, experiments,
and export. A cinematic renderer may establish a world, introduce variation,
follow individuals, demonstrate a mechanism, compress time, reveal population
change, compare conditions, and conclude.

Layer 3 answers:

> How does this medium guide the viewer through the encoded science?

Interactive and cinematic renderers should not be forced into one universal
choreography or replay abstraction.

## Scientific-truth categories

Presentation code must distinguish the following kinds of information.

### Authoritative configuration

Configuration values are real model inputs, but they are not automatically
observed state. For example, configured resource-patch geometry describes where
renewable resource generation may occur; committed resource deposits describe
what resources actually exist in a recorded world state.

When configuration is displayed as explanatory context, the interface must not
present it as though it were an observed state variable.

### Authoritative committed state

Committed observer records describe simulation state at scientific timesteps.
Examples include organism positions, energy, body mass, resources, carcasses, and
selected explicitly recorded per-organism scientific traits.

### Authoritative committed events

Committed telemetry records causal transitions that actually applied. Event
presentation should use this evidence when claiming birth, death, feeding,
reproduction, predation, or another causal interaction rather than inferring
causality from visual proximity or appearance/disappearance alone.

### Derived analytical statistics

A statistic calculated deterministically from committed evidence is valid derived
scientific information, but it should remain conceptually distinct from a raw
observed state value.

### Presentation interpolation

Intermediate animation frames, camera movement, fading, trails, and other
renderer-owned transitions exist only for perceptual continuity. Scientific
metrics, exports, and claims must remain anchored to committed timesteps rather
than treating interpolated frames as independently simulated states.

### Annotation and explanation

Labels, arrows, callouts, and narration interpret evidence. They should state only
claims supported by the scenario rather than silently broadening what the model
has demonstrated.

## Visual-channel rules

Within one view, a visual channel has one scientific or interaction meaning.
Typical reservations are:

| Channel | Intended role |
| --- | --- |
| position | authoritative spatial position |
| fill color | primary scenario-specific scientific encoding |
| size | true physical size when meaningful, otherwise restrained constant |
| shape/silhouette | stable secondary category or biological role |
| marking/pattern | secondary category, genotype, or lineage |
| outline | user selection/focus |
| opacity | presence, de-emphasis, entry/departure transition |
| trail | recent authoritative movement history |
| halo/pulse | temporary event emphasis |
| connector | explicit authoritative interaction or ancestry |
| label | sparse identity or explanation |
| orientation | presentation direction of committed movement |
| z-order | visual hierarchy only, never biological ranking |

If fill color is assigned to a focal strategy, another category such as mating type
must use a secondary channel or move to inspection. The default primary world
should expose few simultaneous encodings rather than trying to visualize every
available model variable.

## Environment and event overlays

A stable world layering order is:

```text
background / world bounds
        ↓
environmental context or habitat
        ↓
environmental state / derived fields
        ↓
resources
        ↓
passive world objects / carcasses
        ↓
organisms
        ↓
event overlays
        ↓
selection / focus
        ↓
annotations
        ↓
HUD / statistics
```

Event effects are temporary overlays on authoritative state. A birth connector,
death fade, feeding emphasis, or predation indicator should not create an
alternate state model. At accelerated playback, low-value effects should be
suppressed rather than accumulating visual noise.

## Motion and time

Scientific timesteps are authoritative. Renderer frames between them are not.

When committed movement evidence is available, renderers should interpolate that
movement without introducing unmodeled biological acceleration. Constant-velocity
interpolation is the conservative default for locomotion; easing remains
appropriate for UI, camera, and purely presentational effects.

Movement trails should follow committed movement segments rather than smoothed
paths that imply positions the organism never occupied. Boundary behavior must be
handled explicitly so wrapping, clamping, rejection, or reflection is not rendered
as a misleading straight traversal.

## Matched comparison

Treatment/control comparisons must keep scientific encoding invariant. When
appropriate, lock focal-variable mappings, colors, value scales, legends, chart
axes, playback conventions, world scale, and camera framing. A renderer must not
create apparent experimental separation through unrelated styling differences.

## Accessibility

Critical categorical distinctions should not depend on hue alone when a readable
secondary cue is feasible. Use color-blind-conscious categorical palettes,
perceptually ordered continuous scales, meaningful diverging scales only when a
scientific midpoint exists, readable legends, sufficient contrast, persistent
non-color selection cues, and reduced-motion behavior that removes decorative
motion without removing scientific information.

## Generic fallback presentation

A spatial biological run does not require a scenario-specific scientific encoding
to remain inspectable. Generic presentation should provide neutral organism
styling, resources, carcasses, committed movement where available, authoritative
entry/departure or birth/death effects where evidence supports them, a timeline,
selection, and basic population/resource/energy information.

Scenario-specific scientific encoding enhances this default rather than becoming a
prerequisite for basic visualization.

## Shared committed evidence for individual traits

Spatial observation deliberately remains about world geometry and selected stable
entity state. When a scenario needs a focal genetic-phenotype trait attached to
individual replayed organisms, use the sibling
`IndividualGeneticTraitRecorder` rather than adding arbitrary trait fields to
`SpatialOrganismSnapshot`.

The join boundary is:

```text
SpatialObservation
    step_index + organism_id + position/state

IndividualGeneticTraitObservation
    step_index + organism_id + selected genetic-phenotype traits

                 ↓
       downstream presentation join
```

The trait recorder is explicitly opt-in and stores only selected integer
genetic-phenotype values. It does not record full genomes or generalize across
developmental, physiological, environmental, and arbitrary callable sources
without a future concrete requirement.

## Current cinematic preparation contract

The cinematic path now has a concrete renderer-owned preparation layer over the
shared evidence boundary. Its responsibility is deliberately narrower than a
generic replay or film-description system:

```text
SpatialObservation
+ IndividualGeneticTraitObservation when requested
+ StepTelemetry
        |
        v
small renderer-neutral scientific encoding values
        |
        v
cinematic prepared primitives / timeline
        |
        v
cinematic renderer and later scenario-specific director
```

`ContinuousTraitEncoding` is the first shared scientific-encoding value justified
by real interactive/cinematic consumers. It records only the committed trait name,
human-readable label, and fixed numeric bounds/normalization. It contains no
renderer colors, materials, widgets, camera, timing, easing, or scene order.

Cinematic preparation joins individual focal evidence to spatial replay by
`(step_index, organism_id)` and fails loudly when the committed histories do not
align. Prepared organism values copy authoritative committed position, body mass,
secondary category, and the optional focal scientific value; they do not retain
live organisms, genomes, phenotypes, worlds, or recorders.

Committed `StepTelemetry` is attached separately from renderer-owned identity
continuity. Appearance and departure are useful for fade/interpolation bookkeeping,
but they are not birth/death evidence. Cinematic event selection therefore uses
actual committed `AppliedEvent` values and preserves commit order rather than
inferring causal events from identity changes or spatial proximity.

Position interpolation is renderer-owned presentation geometry. Its committed
endpoints are exact, intermediate values are not simulation states, and the
interpolation result is never an input to scientific analysis.

The generic cinematic mode remains valid without a focal scientific encoding. A
scenario-directed flagship film is a later choreography concern: representative
episodes, comparison framing, camera movement, act structure, and final claims
must come from the scenario's authoritative scientific storyboard rather than from
this preparation layer.

## Renderer independence

Interactive and cinematic technologies may change independently. The durable
contract is not a specific frontend, plotting library, game engine, or offline
renderer. Both paths consume committed evidence and shared scientific meaning,
then independently implement their own primitives and choreography.

See [Evolution Observability](../observability.md) for committed-record contracts
and [ADR 0009](../decisions/0009-separate-scientific-encoding-from-renderer-choreography.md)
for the rationale behind this responsibility split.
