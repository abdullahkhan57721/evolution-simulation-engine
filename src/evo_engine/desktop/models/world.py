"""Qt item models for renderer-neutral world-presentation primitives."""

from __future__ import annotations

from collections.abc import Sequence
from enum import IntEnum

from PySide6.QtCore import QAbstractListModel, QByteArray, QModelIndex, Qt

from evo_engine.presentation.world import (
    CarcassPrimitive,
    MovementTrail,
    OrganismPrimitive,
    ResourcePrimitive,
)

_INVALID_MODEL_INDEX = QModelIndex()


class _OrganismRole(IntEnum):
    organism_id = int(Qt.ItemDataRole.UserRole) + 1
    x = organism_id + 1
    y = organism_id + 2
    marker_size = organism_id + 3
    selected = organism_id + 4
    body_mass = organism_id + 5
    energy = organism_id + 6
    age = organism_id + 7
    mating_type = organism_id + 8
    focal_trait_value = organism_id + 9
    focal_trait_normalized = organism_id + 10


class WorldOrganismModel(QAbstractListModel):
    """Expose only renderer-facing scalar organism values to QML.

    Adjacent committed frames may preserve delegates when organism identity and
    order are unchanged. QML can then animate changed x/y roles as presentation
    choreography. Any discontinuity uses an atomic model reset instead.
    """

    def __init__(self) -> None:
        super().__init__()
        self._items: tuple[OrganismPrimitive, ...] = ()

    def set_items(
        self,
        items: Sequence[OrganismPrimitive],
        *,
        preserve_delegates: bool = False,
    ) -> bool:
        """Project one committed snapshot and report whether delegates persisted."""
        resolved = tuple(items)
        if not all(isinstance(item, OrganismPrimitive) for item in resolved):
            raise TypeError("items must contain OrganismPrimitive values.")
        old_ids = tuple(item.organism_id for item in self._items)
        new_ids = tuple(item.organism_id for item in resolved)
        can_preserve = bool(resolved) and preserve_delegates and old_ids == new_ids
        if can_preserve:
            self._items = resolved
            top_left = self.index(0, 0)
            bottom_right = self.index(len(resolved) - 1, 0)
            self.dataChanged.emit(top_left, bottom_right, [])
            return True
        self.beginResetModel()
        self._items = resolved
        self.endResetModel()
        return False

    def items(self) -> tuple[OrganismPrimitive, ...]:
        """Return the immutable renderer projection for focused native tests."""
        return self._items

    def rowCount(self, parent: QModelIndex = _INVALID_MODEL_INDEX) -> int:  # noqa: N802
        """Return the number of renderer primitives."""
        return 0 if parent.isValid() else len(self._items)

    def roleNames(self) -> dict[int, QByteArray]:  # noqa: N802
        """Publish stable scalar role names to QML."""
        return {
            int(_OrganismRole.organism_id): QByteArray(b"organismId"),
            int(_OrganismRole.x): QByteArray(b"worldX"),
            int(_OrganismRole.y): QByteArray(b"worldY"),
            int(_OrganismRole.marker_size): QByteArray(b"markerSize"),
            int(_OrganismRole.selected): QByteArray(b"selected"),
            int(_OrganismRole.body_mass): QByteArray(b"bodyMass"),
            int(_OrganismRole.energy): QByteArray(b"energy"),
            int(_OrganismRole.age): QByteArray(b"age"),
            int(_OrganismRole.mating_type): QByteArray(b"matingType"),
            int(_OrganismRole.focal_trait_value): QByteArray(b"focalTraitValue"),
            int(_OrganismRole.focal_trait_normalized): QByteArray(
                b"focalTraitNormalized"
            ),
        }

    def data(self, index: QModelIndex, role: int = int(Qt.ItemDataRole.DisplayRole)):
        """Return one scalar presentation value for a QML role."""
        if not index.isValid() or not 0 <= index.row() < len(self._items):
            return None
        item = self._items[index.row()]
        values = {
            int(_OrganismRole.organism_id): item.organism_id,
            int(_OrganismRole.x): item.x,
            int(_OrganismRole.y): item.y,
            int(_OrganismRole.marker_size): item.marker_size,
            int(_OrganismRole.selected): item.selected,
            int(_OrganismRole.body_mass): item.body_mass,
            int(_OrganismRole.energy): item.energy,
            int(_OrganismRole.age): item.age,
            int(_OrganismRole.mating_type): item.mating_type,
            int(_OrganismRole.focal_trait_value): item.focal_trait_value,
            int(_OrganismRole.focal_trait_normalized): item.focal_trait_normalized,
        }
        return values.get(role)


class _ResourceRole(IntEnum):
    x = int(Qt.ItemDataRole.UserRole) + 1
    y = x + 1
    amount = x + 2


class WorldResourceModel(QAbstractListModel):
    """Expose only renderer-facing scalar resource values to QML."""

    def __init__(self) -> None:
        super().__init__()
        self._items: tuple[ResourcePrimitive, ...] = ()

    def set_items(self, items: Sequence[ResourcePrimitive]) -> None:
        """Replace the presentation snapshot atomically."""
        resolved = tuple(items)
        if not all(isinstance(item, ResourcePrimitive) for item in resolved):
            raise TypeError("items must contain ResourcePrimitive values.")
        self.beginResetModel()
        self._items = resolved
        self.endResetModel()

    def items(self) -> tuple[ResourcePrimitive, ...]:
        return self._items

    def rowCount(self, parent: QModelIndex = _INVALID_MODEL_INDEX) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._items)

    def roleNames(self) -> dict[int, QByteArray]:  # noqa: N802
        return {
            int(_ResourceRole.x): QByteArray(b"worldX"),
            int(_ResourceRole.y): QByteArray(b"worldY"),
            int(_ResourceRole.amount): QByteArray(b"amount"),
        }

    def data(self, index: QModelIndex, role: int = int(Qt.ItemDataRole.DisplayRole)):
        if not index.isValid() or not 0 <= index.row() < len(self._items):
            return None
        item = self._items[index.row()]
        return {
            int(_ResourceRole.x): item.x,
            int(_ResourceRole.y): item.y,
            int(_ResourceRole.amount): item.amount,
        }.get(role)


class _CarcassRole(IntEnum):
    carcass_id = int(Qt.ItemDataRole.UserRole) + 1
    x = carcass_id + 1
    y = carcass_id + 2
    resource_units = carcass_id + 3


class WorldCarcassModel(QAbstractListModel):
    """Expose renderer-facing carcass glyph values to QML."""

    def __init__(self) -> None:
        super().__init__()
        self._items: tuple[CarcassPrimitive, ...] = ()

    def set_items(self, items: Sequence[CarcassPrimitive]) -> None:
        resolved = tuple(items)
        if not all(isinstance(item, CarcassPrimitive) for item in resolved):
            raise TypeError("items must contain CarcassPrimitive values.")
        self.beginResetModel()
        self._items = resolved
        self.endResetModel()

    def items(self) -> tuple[CarcassPrimitive, ...]:
        return self._items

    def rowCount(self, parent: QModelIndex = _INVALID_MODEL_INDEX) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._items)

    def roleNames(self) -> dict[int, QByteArray]:  # noqa: N802
        return {
            int(_CarcassRole.carcass_id): QByteArray(b"carcassId"),
            int(_CarcassRole.x): QByteArray(b"worldX"),
            int(_CarcassRole.y): QByteArray(b"worldY"),
            int(_CarcassRole.resource_units): QByteArray(b"resourceUnits"),
        }

    def data(self, index: QModelIndex, role: int = int(Qt.ItemDataRole.DisplayRole)):
        if not index.isValid() or not 0 <= index.row() < len(self._items):
            return None
        item = self._items[index.row()]
        return {
            int(_CarcassRole.carcass_id): item.carcass_id,
            int(_CarcassRole.x): item.x,
            int(_CarcassRole.y): item.y,
            int(_CarcassRole.resource_units): item.resource_units,
        }.get(role)


class _TrailRole(IntEnum):
    organism_id = int(Qt.ItemDataRole.UserRole) + 1
    points = organism_id + 1


class WorldTrailModel(QAbstractListModel):
    """Expose recent committed trail points without interpolating evidence."""

    def __init__(self) -> None:
        super().__init__()
        self._items: tuple[MovementTrail, ...] = ()

    def set_items(self, items: Sequence[MovementTrail]) -> None:
        resolved = tuple(items)
        if not all(isinstance(item, MovementTrail) for item in resolved):
            raise TypeError("items must contain MovementTrail values.")
        self.beginResetModel()
        self._items = resolved
        self.endResetModel()

    def items(self) -> tuple[MovementTrail, ...]:
        return self._items

    def rowCount(self, parent: QModelIndex = _INVALID_MODEL_INDEX) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._items)

    def roleNames(self) -> dict[int, QByteArray]:  # noqa: N802
        return {
            int(_TrailRole.organism_id): QByteArray(b"organismId"),
            int(_TrailRole.points): QByteArray(b"points"),
        }

    def data(self, index: QModelIndex, role: int = int(Qt.ItemDataRole.DisplayRole)):
        if not index.isValid() or not 0 <= index.row() < len(self._items):
            return None
        item = self._items[index.row()]
        if role == int(_TrailRole.organism_id):
            return item.organism_id
        if role == int(_TrailRole.points):
            return [{"x": x, "y": y} for x, y in item.points]
        return None


__all__ = [
    "WorldCarcassModel",
    "WorldOrganismModel",
    "WorldResourceModel",
    "WorldTrailModel",
]
