"""Tests for attrs-compatible inclusive range validators."""

from collections.abc import Callable

import attrs
import pytest

from evo_engine.validation import attrs_validators


@pytest.mark.parametrize(
    ("factory", "lower", "upper", "valid_values"),
    [
        (attrs_validators.validate_int_in_range, 1, 3, (1, 3)),
        (attrs_validators.validate_number_in_range, 1, 3.0, (1, 3.0)),
        (attrs_validators.validate_float_in_range, 1.0, 3.0, (1.0, 3.0)),
    ],
)
def test_attrs_range_validators_accept_inclusive_endpoints(
    factory: Callable,
    lower: int | float,
    upper: int | float,
    valid_values: tuple[object, object],
) -> None:
    """Test that inclusive range validators accept both endpoints."""

    @attrs.define
    class Model:
        value: object = attrs.field(validator=factory(lower, upper))

    for value in valid_values:
        assert Model(value=value).value is value


@pytest.mark.parametrize(
    ("factory", "lower", "upper", "invalid_value"),
    [
        (attrs_validators.validate_int_in_range, 1, 3, True),
        (attrs_validators.validate_number_in_range, 1, 3.0, True),
        (attrs_validators.validate_float_in_range, 1.0, 3.0, 2),
    ],
)
def test_attrs_range_validators_preserve_exact_value_types(
    factory: Callable,
    lower: int | float,
    upper: int | float,
    invalid_value: object,
) -> None:
    """Test that range fast paths preserve exact value-type requirements."""

    @attrs.define
    class Model:
        value: object = attrs.field(validator=factory(lower, upper))

    with pytest.raises(TypeError):
        Model(value=invalid_value)


@pytest.mark.parametrize(
    ("factory", "lower", "upper", "valid_value"),
    [
        (attrs_validators.validate_int_in_range, True, 3, 2),
        (attrs_validators.validate_number_in_range, True, 3.0, 2),
        (attrs_validators.validate_float_in_range, 1, 3.0, 2.0),
    ],
)
def test_attrs_range_validators_preserve_exact_bound_types(
    factory: Callable,
    lower: object,
    upper: object,
    valid_value: object,
) -> None:
    """Test that invalid bounds cannot slip through numeric Python comparisons."""

    @attrs.define
    class Model:
        value: object = attrs.field(validator=factory(lower, upper))

    with pytest.raises(TypeError):
        Model(value=valid_value)


@pytest.mark.parametrize(
    ("factory", "lower", "upper", "valid_value"),
    [
        (attrs_validators.validate_int_in_range, 3, 1, 2),
        (attrs_validators.validate_number_in_range, 3.0, 1, 2),
        (attrs_validators.validate_float_in_range, 3.0, 1.0, 2.0),
    ],
)
def test_attrs_range_validators_reject_reversed_bounds(
    factory: Callable,
    lower: int | float,
    upper: int | float,
    valid_value: object,
) -> None:
    """Test that a lower bound greater than the upper bound is rejected."""

    @attrs.define
    class Model:
        value: object = attrs.field(validator=factory(lower, upper))

    with pytest.raises(
        ValueError,
        match="lower must be less than or equal to upper",
    ):
        Model(value=valid_value)


def test_attrs_range_validator_runs_on_assignment() -> None:
    """Test that a range validator remains active on attrs assignment."""

    @attrs.define
    class Model:
        value: object = attrs.field(
            validator=attrs_validators.validate_number_in_range(1, 3.0)
        )

    model = Model(value=2)

    with pytest.raises(ValueError):
        model.value = 4
