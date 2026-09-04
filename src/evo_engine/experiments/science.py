"""Durable experimental-science semantics shared by controlled experiments."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Literal

import attrs

from evo_engine.validation import validators

RunRole = Literal["discovery", "confirmation", "representative"]
_RUN_ROLES: frozenset[str] = frozenset({"discovery", "confirmation", "representative"})


@attrs.frozen(slots=True, kw_only=True)
class ScientificRunProvenance:
    """Identify one simulation replicate in a controlled scientific experiment.

    A single simulation run/seed is the replicate represented by this value.
    Organisms observed inside that run are dependent observations, not additional
    experimental replicates.

    Attributes:
        experiment_id: Stable identity of the experiment or assay family.
        scenario_id: Stable identity of the concrete modeled scenario.
        treatment_id: Stable identity of the treatment applied to this run.
        treatment_specification_json: Canonical JSON object containing only the
            scientifically relevant treatment specification.
        seed: Simulation RNG seed identifying the replicate.
        horizon_step_index: Predeclared final committed-state index.
        observation_every_n_steps: State-observation frequency for the run.
        observation_include_step_zero: Whether the observation schedule includes
            the initial committed state at step zero.
        focal_variables: Predeclared scientific variables selected for analysis.
        run_role: Discovery, independent confirmation, or representative-only
            role when that distinction applies.
    """

    experiment_id: str
    scenario_id: str
    treatment_id: str
    treatment_specification_json: str
    seed: int
    horizon_step_index: int
    observation_every_n_steps: int
    observation_include_step_zero: bool
    focal_variables: tuple[str, ...]
    run_role: RunRole | None = None

    def __attrs_post_init__(self) -> None:
        """Validate provenance identities and reproducibility metadata."""
        _validate_nonempty_string(self.experiment_id, name="experiment_id")
        _validate_nonempty_string(self.scenario_id, name="scenario_id")
        _validate_nonempty_string(self.treatment_id, name="treatment_id")
        validators.validate_int(self.seed, name="seed")
        validators.validate_int_ge(
            self.horizon_step_index,
            bound=0,
            name="horizon_step_index",
        )
        validators.validate_int_ge(
            self.observation_every_n_steps,
            bound=1,
            name="observation_every_n_steps",
        )
        validators.validate_bool(
            self.observation_include_step_zero,
            name="observation_include_step_zero",
        )
        validators.validate_tuple(self.focal_variables, name="focal_variables")
        if not self.focal_variables:
            raise ValueError("focal_variables must not be empty.")
        for index, variable in enumerate(self.focal_variables):
            _validate_nonempty_string(variable, name=f"focal_variables[{index}]")
        if len(self.focal_variables) != len(set(self.focal_variables)):
            raise ValueError("focal_variables must not contain duplicates.")

        if self.run_role is not None:
            validated_role = validators.validate_str(self.run_role, name="run_role")
            if validated_role not in _RUN_ROLES:
                raise ValueError(
                    "run_role must be 'discovery', 'confirmation', "
                    "'representative', or None."
                )

        specification_json = _validate_nonempty_string(
            self.treatment_specification_json,
            name="treatment_specification_json",
        )
        try:
            decoded = json.loads(specification_json)
        except json.JSONDecodeError as error:
            raise ValueError(
                "treatment_specification_json must contain valid JSON."
            ) from error
        if type(decoded) is not dict:
            raise ValueError("treatment_specification_json must encode a JSON object.")
        if specification_json != canonical_treatment_specification(decoded):
            raise ValueError(
                "treatment_specification_json must use canonical sorted compact JSON."
            )


@attrs.frozen(slots=True, kw_only=True)
class FixedHorizonTimeToEvent:
    """Represent one observed or explicitly right-censored time-to-event value.

    ``observed_step_index=None`` means the outcome was not observed by the fixed
    committed-state horizon. The value remains right-censored rather than being
    converted to a made-up event time.

    Attributes:
        start_step_index: First committed-state index contributing exposure time.
        horizon_step_index: Fixed final committed-state index for comparison.
        observed_step_index: Committed-state index where the outcome was first
            observed, or ``None`` when right-censored.
    """

    start_step_index: int
    horizon_step_index: int
    observed_step_index: int | None = None

    def __attrs_post_init__(self) -> None:
        """Validate exposure and censoring boundaries."""
        validators.validate_int_ge(
            self.start_step_index,
            bound=0,
            name="start_step_index",
        )
        validators.validate_int_ge(
            self.horizon_step_index,
            bound=self.start_step_index,
            name="horizon_step_index",
        )
        if self.observed_step_index is not None:
            validators.validate_int_ge(
                self.observed_step_index,
                bound=self.start_step_index,
                name="observed_step_index",
            )
            if self.observed_step_index > self.horizon_step_index:
                raise ValueError(
                    "observed_step_index must not exceed horizon_step_index."
                )

    @property
    def right_censored(self) -> bool:
        """Return whether the outcome was unobserved at the fixed horizon."""
        return self.observed_step_index is None

    @property
    def exposure_steps(self) -> int:
        """Return observed exposure through outcome or censoring."""
        end_step_index = (
            self.horizon_step_index
            if self.observed_step_index is None
            else self.observed_step_index
        )
        return end_step_index - self.start_step_index


def canonical_treatment_specification(
    specification: Mapping[str, object],
) -> str:
    """Serialize one scientifically relevant treatment specification canonically.

    Args:
        specification: JSON-compatible mapping containing treatment-relevant
            scientific settings only.

    Returns:
        Stable compact JSON with sorted keys.

    Raises:
        TypeError: If the specification cannot be represented as JSON values.
        ValueError: If it contains non-finite numeric values forbidden by JSON.
    """
    if not isinstance(specification, Mapping):
        raise TypeError("specification must be a mapping.")
    if any(type(key) is not str for key in specification):
        raise TypeError("specification keys must be strings.")
    try:
        return json.dumps(
            dict(specification),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except TypeError as error:
        raise TypeError(
            "specification must contain JSON-serializable values."
        ) from error
    except ValueError as error:
        raise ValueError(
            "specification must contain finite JSON numeric values."
        ) from error


def validate_declared_treatment_difference(
    *,
    control: object,
    normalized_treatment: object,
    declared_difference: str,
) -> None:
    """Fail when a treatment differs outside its explicitly normalized difference.

    Concrete experiments remain responsible for normalizing exactly the setting
    they intend to manipulate. This helper only checks equality afterward; it is
    intentionally not a configuration-diff language.

    Args:
        control: Frozen control specification.
        normalized_treatment: Treatment specification after the one declared
            treatment difference has been replaced with the control value.
        declared_difference: Human-readable name of the intended manipulation.

    Raises:
        ValueError: If any other scientifically relevant setting differs.
    """
    difference = _validate_nonempty_string(
        declared_difference,
        name="declared_difference",
    )
    if normalized_treatment != control:
        raise ValueError(f"Treatment differs from control outside {difference}.")


def _validate_nonempty_string(value: object, *, name: str) -> str:
    validated = validators.validate_str(value, name=name)
    if not validated.strip():
        raise ValueError(f"{name} must not be empty or whitespace-only.")
    return validated
