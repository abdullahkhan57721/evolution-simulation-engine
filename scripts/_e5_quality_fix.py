from pathlib import Path

source = Path("src/evo_engine/experiments/e5_drift.py")
text = source.read_text()
old = '''    def __attrs_post_init__(self) -> None:
        """Validate complete composition and explicit extinction semantics."""
        if len(self.counts) != 2 or len(self.frequencies) != 2:
            raise ValueError("E5 composition must contain exactly two groups.")
        for index, count in enumerate(self.counts):
            validators.validate_int_ge(count, bound=0, name=f"counts[{index}]")
        if sum(self.counts) != self.population_size:
            raise ValueError("lineage counts must equal complete population size.")
        if self.population_size == 0:
            if any(value is not None for value in self.frequencies):
                raise ValueError("extinct lineage frequencies must be undefined.")
            return
        if any(value is None for value in self.frequencies):
            raise ValueError("nonempty lineage frequencies must be defined.")
        defined = tuple(value for value in self.frequencies if value is not None)
        if any(
            not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in defined
        ):
            raise ValueError("defined lineage frequencies must be finite in [0, 1].")
        if not math.isclose(sum(defined), 1.0):
            raise ValueError("defined lineage frequencies must sum to one.")
'''
new = '''    def __attrs_post_init__(self) -> None:
        """Validate complete composition and explicit extinction semantics."""
        if len(self.counts) != 2 or len(self.frequencies) != 2:
            raise ValueError("E5 composition must contain exactly two groups.")
        for index, count in enumerate(self.counts):
            validators.validate_int_ge(count, bound=0, name=f"counts[{index}]")
        if sum(self.counts) != self.population_size:
            raise ValueError("lineage counts must equal complete population size.")
        _validate_lineage_frequencies(
            population_size=self.population_size,
            frequencies=self.frequencies,
        )
'''
if old not in text:
    raise SystemExit("expected E5 composition validation block not found")
text = text.replace(old, new, 1)

marker = '''    def frequency(self, group: E5Group) -> float | None:
        """Return the committed frequency for one analysis group."""
        return self.frequencies[_group_index(group)]


@attrs.frozen(slots=True, kw_only=True)
class E5ReplicateOutcome:
'''
replacement = '''    def frequency(self, group: E5Group) -> float | None:
        """Return the committed frequency for one analysis group."""
        return self.frequencies[_group_index(group)]


def _validate_lineage_frequencies(
    *,
    population_size: int,
    frequencies: tuple[float | None, float | None],
) -> None:
    """Validate extinction-aware E5 lineage-frequency semantics."""
    if population_size == 0:
        if frequencies != (None, None):
            raise ValueError("extinct lineage frequencies must be undefined.")
        return
    if frequencies[0] is None or frequencies[1] is None:
        raise ValueError("nonempty lineage frequencies must be defined.")
    _validate_defined_lineage_frequencies((frequencies[0], frequencies[1]))


def _validate_defined_lineage_frequencies(frequencies: tuple[float, float]) -> None:
    """Validate defined E5 lineage frequencies."""
    if any(
        not math.isfinite(value) or not 0.0 <= value <= 1.0
        for value in frequencies
    ):
        raise ValueError("defined lineage frequencies must be finite in [0, 1].")
    if not math.isclose(sum(frequencies), 1.0):
        raise ValueError("defined lineage frequencies must sum to one.")


@attrs.frozen(slots=True, kw_only=True)
class E5ReplicateOutcome:
'''
if marker not in text:
    raise SystemExit("expected E5 composition class marker not found")
source.write_text(text.replace(marker, replacement, 1))

tests = Path("tests/experiments/test_e5_drift.py")
test_text = tests.read_text()
stale_import = "    assignment_phase_for_replicate,\n"
if stale_import not in test_text:
    raise SystemExit("expected stale assignment-phase test import not found")
tests.write_text(test_text.replace(stale_import, "", 1))
