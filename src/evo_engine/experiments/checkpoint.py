"""Persist and resume exact reference-ecology checkpoints."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import pickle
import platform
import tempfile
from importlib import metadata
from pathlib import Path
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile

import attrs

from evo_engine.presets import ReferenceEcology
from evo_engine.validation import validators

_PACKAGE_NAME = "evolution-simulation-engine"
_CHECKPOINT_FORMAT = "evolution-simulation-engine.reference-checkpoint"
_CHECKPOINT_FORMAT_VERSION = 1
_MANIFEST_NAME = "manifest.json"
_PAYLOAD_NAME = "reference_ecology.pkl"


@attrs.frozen(slots=True, kw_only=True)
class ReferenceCheckpointManifest:
    """Describe a saved reference-ecology checkpoint without loading its payload.

    Attributes:
        format_version: Checkpoint archive format version.
        engine_version: Installed engine package version at save time.
        python_version: Python interpreter version at save time.
        step_index: Completed simulation step stored in the checkpoint.
        config_json: Canonical JSON representation of the reference configuration.
        payload_sha256: SHA-256 integrity digest of the serialized ecology payload.
        rng_state_sha256: SHA-256 fingerprint of the exact random-generator state.
    """

    format_version: int
    engine_version: str
    python_version: str
    step_index: int
    config_json: str
    payload_sha256: str
    rng_state_sha256: str

    def __attrs_post_init__(self) -> None:
        """Validate manifest values."""
        validators.validate_int_ge(
            self.format_version,
            bound=1,
            name="format_version",
        )
        _validate_nonempty_string(self.engine_version, name="engine_version")
        _validate_nonempty_string(self.python_version, name="python_version")
        validators.validate_int_ge(self.step_index, bound=0, name="step_index")
        _validate_nonempty_string(self.config_json, name="config_json")
        _validate_sha256(self.payload_sha256, name="payload_sha256")
        _validate_sha256(self.rng_state_sha256, name="rng_state_sha256")


def write_reference_checkpoint(
    ecology: ReferenceEcology,
    path: str | Path,
) -> Path:
    """Atomically write an exact reference-ecology checkpoint archive.

    The binary payload preserves the complete reference ecology, including the
    authoritative world, private organism/carcass ID allocators, engine wiring,
    recorder histories, committed telemetry, and ``random.Random`` state. A JSON
    manifest stores diagnostics and integrity fingerprints alongside the payload.

    Args:
        ecology: Reference ecology to checkpoint.
        path: Destination archive path.

    Returns:
        Resolved destination path.

    Raises:
        TypeError: If ecology is not a ReferenceEcology.
    """
    if not isinstance(ecology, ReferenceEcology):
        raise TypeError("ecology must be a ReferenceEcology.")

    destination = _prepare_destination(path)
    payload = pickle.dumps(ecology, protocol=pickle.HIGHEST_PROTOCOL)
    manifest = _build_manifest(ecology, payload=payload)
    _write_archive_atomically(destination, manifest=manifest, payload=payload)
    return destination


def read_reference_checkpoint_manifest(
    path: str | Path,
) -> ReferenceCheckpointManifest:
    """Read checkpoint metadata without unpickling the simulation payload.

    Args:
        path: Existing checkpoint archive path.

    Returns:
        Validated checkpoint manifest.

    Raises:
        ValueError: If the archive or manifest is invalid or unsupported.
    """
    source = _prepare_source(path)
    try:
        with ZipFile(source, "r") as archive:
            return _read_manifest(archive)
    except (BadZipFile, KeyError, json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError("Invalid reference checkpoint archive.") from error


def load_reference_checkpoint(path: str | Path) -> ReferenceEcology:
    """Load an exact reference ecology from a trusted checkpoint archive.

    Checkpoint payloads use Python pickle so they can preserve complete object
    identity and RNG state. Only load checkpoint files created by a trusted
    source. The SHA-256 digest detects accidental corruption; it is not an
    authenticity or security signature.

    Args:
        path: Existing trusted checkpoint archive path.

    Returns:
        Restored reference ecology ready to continue running.

    Raises:
        ValueError: If the archive, manifest, checksum, or restored state is
            invalid or unsupported.
    """
    source = _prepare_source(path)
    manifest, payload = _read_checkpoint(source)
    _require_matching_digest(
        payload,
        expected=manifest.payload_sha256,
        name="checkpoint payload",
    )

    try:
        ecology = pickle.loads(payload)
    except (pickle.UnpicklingError, AttributeError, EOFError, ImportError) as error:
        raise ValueError("Checkpoint payload could not be restored.") from error

    if not isinstance(ecology, ReferenceEcology):
        raise ValueError("Checkpoint payload does not contain a ReferenceEcology.")
    _validate_restored_ecology(ecology, manifest=manifest)
    return ecology


def resume_reference_checkpoint(path: str | Path) -> ReferenceEcology:
    """Load a trusted checkpoint and run it to its configured stopping condition.

    Args:
        path: Existing trusted checkpoint archive path.

    Returns:
        Restored reference ecology after continuation completes.
    """
    ecology = load_reference_checkpoint(path)
    ecology.engine.run(ecology.simulation)
    return ecology


def _build_manifest(
    ecology: ReferenceEcology,
    *,
    payload: bytes,
) -> ReferenceCheckpointManifest:
    return ReferenceCheckpointManifest(
        format_version=_CHECKPOINT_FORMAT_VERSION,
        engine_version=_engine_version(),
        python_version=platform.python_version(),
        step_index=ecology.simulation.state.step_index,
        config_json=_canonical_config_json(ecology),
        payload_sha256=_sha256(payload),
        rng_state_sha256=_rng_state_sha256(ecology),
    )


def _write_archive_atomically(
    destination: Path,
    *,
    manifest: ReferenceCheckpointManifest,
    payload: bytes,
) -> None:
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
    )
    os.close(file_descriptor)
    temporary_path = Path(temporary_name)
    try:
        with ZipFile(temporary_path, "w", compression=ZIP_DEFLATED) as archive:
            archive.writestr(
                _MANIFEST_NAME,
                json.dumps(
                    _manifest_dict(manifest),
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
            )
            archive.writestr(_PAYLOAD_NAME, payload)
        os.replace(temporary_path, destination)
    finally:
        temporary_path.unlink(missing_ok=True)


def _read_checkpoint(
    source: Path,
) -> tuple[ReferenceCheckpointManifest, bytes]:
    try:
        with ZipFile(source, "r") as archive:
            manifest = _read_manifest(archive)
            payload = archive.read(_PAYLOAD_NAME)
    except (BadZipFile, KeyError, json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError("Invalid reference checkpoint archive.") from error
    return manifest, payload


def _read_manifest(archive: ZipFile) -> ReferenceCheckpointManifest:
    raw_manifest = json.loads(archive.read(_MANIFEST_NAME).decode("utf-8"))
    if not isinstance(raw_manifest, dict):
        raise ValueError("Checkpoint manifest must be a JSON object.")
    if raw_manifest.get("format") != _CHECKPOINT_FORMAT:
        raise ValueError("Checkpoint format identifier is invalid.")

    try:
        manifest = ReferenceCheckpointManifest(
            format_version=raw_manifest["format_version"],
            engine_version=raw_manifest["engine_version"],
            python_version=raw_manifest["python_version"],
            step_index=raw_manifest["step_index"],
            config_json=raw_manifest["config_json"],
            payload_sha256=raw_manifest["payload_sha256"],
            rng_state_sha256=raw_manifest["rng_state_sha256"],
        )
    except (KeyError, TypeError) as error:
        raise ValueError("Checkpoint manifest is incomplete or invalid.") from error

    if manifest.format_version != _CHECKPOINT_FORMAT_VERSION:
        raise ValueError(
            "Unsupported reference checkpoint format version "
            f"{manifest.format_version}."
        )
    return manifest


def _manifest_dict(manifest: ReferenceCheckpointManifest) -> dict[str, object]:
    return {
        "format": _CHECKPOINT_FORMAT,
        "format_version": manifest.format_version,
        "engine_version": manifest.engine_version,
        "python_version": manifest.python_version,
        "step_index": manifest.step_index,
        "config_json": manifest.config_json,
        "payload_sha256": manifest.payload_sha256,
        "rng_state_sha256": manifest.rng_state_sha256,
    }


def _validate_restored_ecology(
    ecology: ReferenceEcology,
    *,
    manifest: ReferenceCheckpointManifest,
) -> None:
    if ecology.simulation.state.step_index != manifest.step_index:
        raise ValueError(
            "Checkpoint step index does not match restored simulation state."
        )
    if _canonical_config_json(ecology) != manifest.config_json:
        raise ValueError("Checkpoint configuration does not match restored ecology.")
    _require_matching_digest(
        pickle.dumps(
            ecology.simulation.state.rng.getstate(),
            protocol=pickle.HIGHEST_PROTOCOL,
        ),
        expected=manifest.rng_state_sha256,
        name="RNG state",
    )


def _rng_state_sha256(ecology: ReferenceEcology) -> str:
    rng_state = pickle.dumps(
        ecology.simulation.state.rng.getstate(),
        protocol=pickle.HIGHEST_PROTOCOL,
    )
    return _sha256(rng_state)


def _require_matching_digest(
    content: bytes,
    *,
    expected: str,
    name: str,
) -> None:
    actual = _sha256(content)
    if not hmac.compare_digest(actual, expected):
        raise ValueError(f"{name} SHA-256 digest does not match checkpoint manifest.")


def _canonical_config_json(ecology: ReferenceEcology) -> str:
    return json.dumps(
        attrs.asdict(ecology.config),
        sort_keys=True,
        separators=(",", ":"),
    )


def _engine_version() -> str:
    try:
        return metadata.version(_PACKAGE_NAME)
    except metadata.PackageNotFoundError:
        return "unknown"


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _prepare_destination(path: str | Path) -> Path:
    destination = Path(path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    return destination


def _prepare_source(path: str | Path) -> Path:
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise ValueError(f"Checkpoint path is not an existing file: {source}")
    return source


def _validate_nonempty_string(value: object, *, name: str) -> str:
    validated = validators.validate_str(value, name=name)
    if not validated.strip():
        raise ValueError(f"{name} must not be empty or whitespace-only.")
    return validated


def _validate_sha256(value: object, *, name: str) -> str:
    validated = _validate_nonempty_string(value, name=name)
    if len(validated) != 64 or any(
        character not in "0123456789abcdef" for character in validated
    ):
        raise ValueError(f"{name} must be a lowercase SHA-256 hexadecimal digest.")
    return validated
