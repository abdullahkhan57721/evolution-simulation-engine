# Exact Checkpoint, Save, and Resume

Reference ecologies can be paused to disk and resumed without rebuilding their
state from summaries.

```python
from evo_engine.experiments import (
    resume_reference_checkpoint,
    write_reference_checkpoint,
)
from evo_engine.presets import ReferenceEcologyConfig, build_reference_ecology

config = ReferenceEcologyConfig(max_steps=1_000, seed=101)
ecology = build_reference_ecology(config)

# After running some committed steps:
write_reference_checkpoint(ecology, "outputs/run.evochk")

# In the same or a later Python process:
ecology = resume_reference_checkpoint("outputs/run.evochk")
```

## What an exact checkpoint preserves

The checkpoint payload preserves the complete connected `ReferenceEcology`
object graph rather than reconstructing a simulation from exported statistics.
That includes:

- the authoritative `WorldState`, including organisms, carcasses, resources,
  and private next-ID allocators,
- the current `SimulationState.step_index`,
- the exact `random.Random` state,
- genetic architecture and behavior configuration,
- the configured engine, lifecycle stages, processes, and resolvers,
- population and genetic-composition histories,
- committed event telemetry, and
- pedigree and lifetime-fitness state.

Because Python pickle preserves shared references within one object graph, the
recorder objects exposed by `ReferenceEcology` remain the same recorder objects
attached to the restored engine.

Calling `resume_reference_checkpoint()` loads the checkpoint and invokes the
restored engine until its already-configured stopping condition is reached.
Recorder duplicate guards ensure that the saved committed step is not recorded a
second time when execution resumes.

## Archive format and integrity

A checkpoint is a ZIP archive containing:

- `manifest.json`, a safe-to-read metadata document, and
- `reference_ecology.pkl`, the exact binary object payload.

The manifest records the checkpoint-format version, package version, Python
version, canonical reference configuration JSON, completed step index, payload
SHA-256 digest, and a separate SHA-256 fingerprint of the serialized RNG state.

You can inspect the manifest without unpickling the simulation:

```python
from evo_engine.experiments import read_reference_checkpoint_manifest

manifest = read_reference_checkpoint_manifest("outputs/run.evochk")
print(manifest.step_index)
print(manifest.rng_state_sha256)
```

Writes are atomic: the archive is completed in a temporary file in the target
directory and then moved into place with `os.replace()`. A failed write therefore
does not leave a partially written file at the requested destination.

## Trust and compatibility

Checkpoint payloads use Python pickle because exact continuation requires
preserving a rich Python object graph and the RNG state, not merely portable
analysis data. **Only load checkpoint files from a trusted source.** The SHA-256
checks detect accidental corruption, but they are not cryptographic signatures
and do not make an untrusted pickle safe.

Checkpoints are intended for exact continuation with compatible engine code.
The manifest stores engine and Python versions for diagnostics, while the archive
format version allows future checkpoint-layout migrations to be detected rather
than silently misread. For long-term or cross-language analysis, use the JSON and
CSV experiment exports instead of checkpoint files.
