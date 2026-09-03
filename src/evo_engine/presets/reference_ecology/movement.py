"""Typed exploration-movement configuration for the reference ecology."""

from __future__ import annotations

from typing import Literal, TypeAlias

import attrs

from evo_engine.validation import attrs_validators


@attrs.frozen(slots=True, kw_only=True)
class ReferenceMooreMovement:
    """Configure adjacent Moore-neighborhood exploration movement."""

    kind: Literal["moore"] = attrs.field(default="moore", init=False)


@attrs.frozen(slots=True, kw_only=True)
class ReferenceVonNeumannMovement:
    """Configure one-cell orthogonal exploration movement."""

    kind: Literal["von_neumann"] = attrs.field(default="von_neumann", init=False)


@attrs.frozen(slots=True, kw_only=True)
class ReferenceUniformMovement:
    """Configure uniform exploration movement within the speed limit."""

    kind: Literal["uniform"] = attrs.field(default="uniform", init=False)


@attrs.frozen(slots=True, kw_only=True)
class ReferenceGaussianMovement:
    """Configure Gaussian exploration movement within the speed limit.

    Attributes:
        standard_deviation: Standard deviation used to sample each movement axis.
    """

    kind: Literal["gaussian"] = attrs.field(default="gaussian", init=False)
    standard_deviation: int = attrs.field(
        default=1,
        validator=attrs_validators.validate_int_ge(0),
    )


ReferenceExplorationMovement: TypeAlias = (
    ReferenceMooreMovement
    | ReferenceVonNeumannMovement
    | ReferenceUniformMovement
    | ReferenceGaussianMovement
)
