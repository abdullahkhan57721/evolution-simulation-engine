"""Spatial placement models for renewable environmental resources."""

from __future__ import annotations

import random
from typing import Protocol

import attrs

from evo_engine.validation import attrs_validators, validators


class ResourcePlacementModel(Protocol):
    """Choose one world coordinate for a generated resource deposit."""

    def choose_position(
        self,
        *,
        width: int,
        height: int,
        rng: random.Random,
    ) -> tuple[int, int]:
        """Return one valid resource-deposit coordinate.

        Args:
            width: World width in grid cells.
            height: World height in grid cells.
            rng: Simulation-owned random number generator.

        Returns:
            Selected ``(x, y)`` world coordinate.
        """
        ...


@attrs.frozen(slots=True, kw_only=True)
class UniformResourcePlacement:
    """Place each generated resource deposit uniformly across the world grid."""

    def choose_position(
        self,
        *,
        width: int,
        height: int,
        rng: random.Random,
    ) -> tuple[int, int]:
        """Return one uniformly selected world coordinate.

        The two ``randrange`` calls intentionally preserve the historical
        ``ResourceGeneration`` RNG sequence for the default placement behavior.

        Args:
            width: World width in grid cells.
            height: World height in grid cells.
            rng: Simulation-owned random number generator.

        Returns:
            Uniformly selected ``(x, y)`` coordinate.
        """
        validated_width = validators.validate_int_ge(width, bound=1, name="width")
        validated_height = validators.validate_int_ge(
            height,
            bound=1,
            name="height",
        )
        return (
            rng.randrange(validated_width),
            rng.randrange(validated_height),
        )


@attrs.frozen(slots=True, kw_only=True)
class ResourcePatch:
    """Define one weighted circular resource patch on the world grid.

    A patch contains in-bounds grid cells whose squared Euclidean distance from
    ``(center_x, center_y)`` is at most ``radius ** 2``. A zero-radius patch
    therefore represents exactly its center cell.

    Attributes:
        center_x: Horizontal grid coordinate of the patch center.
        center_y: Vertical grid coordinate of the patch center.
        radius: Nonnegative Euclidean patch radius in grid cells.
        weight: Positive relative probability of selecting this patch.
    """

    center_x: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    center_y: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    radius: int = attrs.field(
        default=0,
        validator=attrs_validators.validate_int_ge(0),
    )
    weight: int = attrs.field(
        default=1,
        validator=attrs_validators.validate_int_gt(0),
    )


@attrs.frozen(slots=True, kw_only=True)
class PatchyResourcePlacement:
    """Place resource deposits inside one or more weighted spatial patches.

    Patch geometry is intersected with the finite world grid. This gives edge
    patches clean truncated-disk semantics without clamping sampled coordinates
    or using rejection loops.

    Attributes:
        patches: Nonempty tuple of configured resource patches.
    """

    patches: tuple[ResourcePatch, ...]

    def __attrs_post_init__(self) -> None:
        """Validate patch collection type and contents."""
        validators.validate_tuple(self.patches, name="patches")
        if not self.patches:
            raise ValueError("patches must contain at least one ResourcePatch.")
        for index, patch in enumerate(self.patches):
            if not isinstance(patch, ResourcePatch):
                raise TypeError(f"patches[{index}] must be a ResourcePatch.")

    def choose_position(
        self,
        *,
        width: int,
        height: int,
        rng: random.Random,
    ) -> tuple[int, int]:
        """Return one weighted patch coordinate using the supplied RNG.

        Args:
            width: World width in grid cells.
            height: World height in grid cells.
            rng: Simulation-owned random number generator.

        Returns:
            Selected ``(x, y)`` coordinate inside the selected patch and world.

        Raises:
            ValueError: If a configured patch center lies outside the world.
        """
        validated_width = validators.validate_int_ge(width, bound=1, name="width")
        validated_height = validators.validate_int_ge(
            height,
            bound=1,
            name="height",
        )
        for index, patch in enumerate(self.patches):
            if patch.center_x >= validated_width or patch.center_y >= validated_height:
                raise ValueError(
                    f"patches[{index}] center ({patch.center_x}, {patch.center_y}) "
                    f"must lie within world bounds {validated_width}x{validated_height}."
                )

        selected_patch = self._choose_patch(rng)
        cells = _patch_cells(
            selected_patch,
            width=validated_width,
            height=validated_height,
        )
        return rng.choice(cells)

    def _choose_patch(self, rng: random.Random) -> ResourcePatch:
        total_weight = sum(patch.weight for patch in self.patches)
        ticket = rng.randrange(total_weight)
        cumulative_weight = 0
        for patch in self.patches:
            cumulative_weight += patch.weight
            if ticket < cumulative_weight:
                return patch
        raise RuntimeError("weighted patch selection failed unexpectedly.")


def _patch_cells(
    patch: ResourcePatch,
    *,
    width: int,
    height: int,
) -> tuple[tuple[int, int], ...]:
    min_x = max(0, patch.center_x - patch.radius)
    max_x = min(width - 1, patch.center_x + patch.radius)
    min_y = max(0, patch.center_y - patch.radius)
    max_y = min(height - 1, patch.center_y + patch.radius)
    radius_squared = patch.radius * patch.radius

    return tuple(
        (x, y)
        for y in range(min_y, max_y + 1)
        for x in range(min_x, max_x + 1)
        if (x - patch.center_x) ** 2 + (y - patch.center_y) ** 2
        <= radius_squared
    )


__all__ = [
    "PatchyResourcePlacement",
    "ResourcePatch",
    "ResourcePlacementModel",
    "UniformResourcePlacement",
]
