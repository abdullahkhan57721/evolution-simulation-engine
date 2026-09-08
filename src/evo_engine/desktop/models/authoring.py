"""Qt item models for curated native Workbench authoring values."""

from __future__ import annotations

from collections.abc import Sequence
from enum import IntEnum

import attrs
from PySide6.QtCore import QAbstractListModel, QByteArray, QModelIndex, Qt

_INVALID_MODEL_INDEX = QModelIndex()


@attrs.frozen(slots=True, kw_only=True)
class MeaningItem:
    """One user-facing scientific meaning value."""

    label: str
    value: str


@attrs.frozen(slots=True, kw_only=True)
class SemanticDiffItem:
    """One existing Workbench semantic-diff change rendered for QML."""

    group: str
    label: str
    before: str
    after: str
    tone: str = "neutral"


@attrs.frozen(slots=True, kw_only=True)
class EvidenceItem:
    """One concrete evidence choice in scientific vocabulary."""

    evidence_id: str
    label: str
    meaning: str
    enables: str
    selected: bool
    required: bool
    editable: bool


@attrs.frozen(slots=True, kw_only=True)
class ExperimentRunItem:
    """One authoritative expanded E3/E4 run row."""

    maximum_speed: str = ""
    seed: str = ""
    role: str = ""
    environment: str = ""
    resource_geography: str = ""
    standing_composition: str = ""
    founder_order: str = ""


@attrs.frozen(slots=True, kw_only=True)
class FactorLevelItem:
    """One supported E3 maximum-speed factor level."""

    value: int
    selected: bool


class _MeaningRole(IntEnum):
    label = int(Qt.ItemDataRole.UserRole) + 1
    item_value = label + 1


class MeaningListModel(QAbstractListModel):
    """Expose label/value scientific meaning rows to QML."""

    def __init__(self) -> None:
        super().__init__()
        self._items: tuple[MeaningItem, ...] = ()

    def set_items(self, items: Sequence[MeaningItem]) -> None:
        resolved = tuple(items)
        if not all(isinstance(item, MeaningItem) for item in resolved):
            raise TypeError("items must contain MeaningItem values.")
        self.beginResetModel()
        self._items = resolved
        self.endResetModel()

    def items(self) -> tuple[MeaningItem, ...]:
        return self._items

    def rowCount(self, parent: QModelIndex = _INVALID_MODEL_INDEX) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._items)

    def roleNames(self) -> dict[int, QByteArray]:  # noqa: N802
        return {
            int(_MeaningRole.label): QByteArray(b"label"),
            int(_MeaningRole.item_value): QByteArray(b"value"),
        }

    def data(self, index: QModelIndex, role: int = int(Qt.ItemDataRole.DisplayRole)):
        if not index.isValid() or not 0 <= index.row() < len(self._items):
            return None
        item = self._items[index.row()]
        return {
            int(_MeaningRole.label): item.label,
            int(_MeaningRole.item_value): item.value,
        }.get(role)


class _DiffRole(IntEnum):
    group = int(Qt.ItemDataRole.UserRole) + 1
    label = group + 1
    before = group + 2
    after = group + 3
    tone = group + 4


class SemanticDiffModel(QAbstractListModel):
    """Expose existing recipe-scoped semantic changes to QML."""

    def __init__(self) -> None:
        super().__init__()
        self._items: tuple[SemanticDiffItem, ...] = ()

    def set_items(self, items: Sequence[SemanticDiffItem]) -> None:
        resolved = tuple(items)
        if not all(isinstance(item, SemanticDiffItem) for item in resolved):
            raise TypeError("items must contain SemanticDiffItem values.")
        self.beginResetModel()
        self._items = resolved
        self.endResetModel()

    def items(self) -> tuple[SemanticDiffItem, ...]:
        return self._items

    def rowCount(self, parent: QModelIndex = _INVALID_MODEL_INDEX) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._items)

    def roleNames(self) -> dict[int, QByteArray]:  # noqa: N802
        return {
            int(_DiffRole.group): QByteArray(b"groupName"),
            int(_DiffRole.label): QByteArray(b"label"),
            int(_DiffRole.before): QByteArray(b"beforeValue"),
            int(_DiffRole.after): QByteArray(b"afterValue"),
            int(_DiffRole.tone): QByteArray(b"tone"),
        }

    def data(self, index: QModelIndex, role: int = int(Qt.ItemDataRole.DisplayRole)):
        if not index.isValid() or not 0 <= index.row() < len(self._items):
            return None
        item = self._items[index.row()]
        return {
            int(_DiffRole.group): item.group,
            int(_DiffRole.label): item.label,
            int(_DiffRole.before): item.before,
            int(_DiffRole.after): item.after,
            int(_DiffRole.tone): item.tone,
        }.get(role)


class _EvidenceRole(IntEnum):
    evidence_id = int(Qt.ItemDataRole.UserRole) + 1
    label = evidence_id + 1
    meaning = evidence_id + 2
    enables = evidence_id + 3
    selected = evidence_id + 4
    required = evidence_id + 5
    editable = evidence_id + 6


class EvidenceOptionModel(QAbstractListModel):
    """Expose only concrete scientific evidence choices to QML."""

    def __init__(self) -> None:
        super().__init__()
        self._items: tuple[EvidenceItem, ...] = ()

    def set_items(self, items: Sequence[EvidenceItem]) -> None:
        resolved = tuple(items)
        if not all(isinstance(item, EvidenceItem) for item in resolved):
            raise TypeError("items must contain EvidenceItem values.")
        self.beginResetModel()
        self._items = resolved
        self.endResetModel()

    def items(self) -> tuple[EvidenceItem, ...]:
        return self._items

    def rowCount(self, parent: QModelIndex = _INVALID_MODEL_INDEX) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._items)

    def roleNames(self) -> dict[int, QByteArray]:  # noqa: N802
        return {
            int(_EvidenceRole.evidence_id): QByteArray(b"evidenceId"),
            int(_EvidenceRole.label): QByteArray(b"label"),
            int(_EvidenceRole.meaning): QByteArray(b"meaning"),
            int(_EvidenceRole.enables): QByteArray(b"enables"),
            int(_EvidenceRole.selected): QByteArray(b"selected"),
            int(_EvidenceRole.required): QByteArray(b"required"),
            int(_EvidenceRole.editable): QByteArray(b"editable"),
        }

    def data(self, index: QModelIndex, role: int = int(Qt.ItemDataRole.DisplayRole)):
        if not index.isValid() or not 0 <= index.row() < len(self._items):
            return None
        item = self._items[index.row()]
        return {
            int(_EvidenceRole.evidence_id): item.evidence_id,
            int(_EvidenceRole.label): item.label,
            int(_EvidenceRole.meaning): item.meaning,
            int(_EvidenceRole.enables): item.enables,
            int(_EvidenceRole.selected): item.selected,
            int(_EvidenceRole.required): item.required,
            int(_EvidenceRole.editable): item.editable,
        }.get(role)


class _RunRole(IntEnum):
    maximum_speed = int(Qt.ItemDataRole.UserRole) + 1
    seed = maximum_speed + 1
    role = maximum_speed + 2
    environment = maximum_speed + 3
    resource_geography = maximum_speed + 4
    standing_composition = maximum_speed + 5
    founder_order = maximum_speed + 6


class ExperimentRunModel(QAbstractListModel):
    """Expose authoritative expanded E3/E4 rows to QML."""

    def __init__(self) -> None:
        super().__init__()
        self._items: tuple[ExperimentRunItem, ...] = ()

    def set_items(self, items: Sequence[ExperimentRunItem]) -> None:
        resolved = tuple(items)
        if not all(isinstance(item, ExperimentRunItem) for item in resolved):
            raise TypeError("items must contain ExperimentRunItem values.")
        self.beginResetModel()
        self._items = resolved
        self.endResetModel()

    def items(self) -> tuple[ExperimentRunItem, ...]:
        return self._items

    def rowCount(self, parent: QModelIndex = _INVALID_MODEL_INDEX) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._items)

    def roleNames(self) -> dict[int, QByteArray]:  # noqa: N802
        return {
            int(_RunRole.maximum_speed): QByteArray(b"maximumSpeed"),
            int(_RunRole.seed): QByteArray(b"seed"),
            int(_RunRole.role): QByteArray(b"roleName"),
            int(_RunRole.environment): QByteArray(b"environment"),
            int(_RunRole.resource_geography): QByteArray(b"resourceGeography"),
            int(_RunRole.standing_composition): QByteArray(b"standingComposition"),
            int(_RunRole.founder_order): QByteArray(b"founderOrder"),
        }

    def data(self, index: QModelIndex, role: int = int(Qt.ItemDataRole.DisplayRole)):
        if not index.isValid() or not 0 <= index.row() < len(self._items):
            return None
        item = self._items[index.row()]
        return {
            int(_RunRole.maximum_speed): item.maximum_speed,
            int(_RunRole.seed): item.seed,
            int(_RunRole.role): item.role,
            int(_RunRole.environment): item.environment,
            int(_RunRole.resource_geography): item.resource_geography,
            int(_RunRole.standing_composition): item.standing_composition,
            int(_RunRole.founder_order): item.founder_order,
        }.get(role)


class _FactorLevelRole(IntEnum):
    level_value = int(Qt.ItemDataRole.UserRole) + 1
    selected = level_value + 1


class FactorLevelModel(QAbstractListModel):
    """Expose the bounded supported E3 factor levels to QML."""

    def __init__(self) -> None:
        super().__init__()
        self._items: tuple[FactorLevelItem, ...] = ()

    def set_items(self, items: Sequence[FactorLevelItem]) -> None:
        resolved = tuple(items)
        if not all(isinstance(item, FactorLevelItem) for item in resolved):
            raise TypeError("items must contain FactorLevelItem values.")
        self.beginResetModel()
        self._items = resolved
        self.endResetModel()

    def items(self) -> tuple[FactorLevelItem, ...]:
        return self._items

    def rowCount(self, parent: QModelIndex = _INVALID_MODEL_INDEX) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._items)

    def roleNames(self) -> dict[int, QByteArray]:  # noqa: N802
        return {
            int(_FactorLevelRole.level_value): QByteArray(b"levelValue"),
            int(_FactorLevelRole.selected): QByteArray(b"selected"),
        }

    def data(self, index: QModelIndex, role: int = int(Qt.ItemDataRole.DisplayRole)):
        if not index.isValid() or not 0 <= index.row() < len(self._items):
            return None
        item = self._items[index.row()]
        return {
            int(_FactorLevelRole.level_value): item.value,
            int(_FactorLevelRole.selected): item.selected,
        }.get(role)


__all__ = [
    "EvidenceItem",
    "EvidenceOptionModel",
    "ExperimentRunItem",
    "ExperimentRunModel",
    "FactorLevelItem",
    "FactorLevelModel",
    "MeaningItem",
    "MeaningListModel",
    "SemanticDiffItem",
    "SemanticDiffModel",
]
