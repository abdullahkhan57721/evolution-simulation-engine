"""Tests for the general runtime validators."""

import math

import pytest

from evo_engine.validation import validators

# Type validators


@pytest.mark.parametrize(
    "value",
    [0, 1, -10, 1.5, "text", [], (), set(), False],
)
def test_validate_not_none_accepts_non_none_values(value: object) -> None:
    """Test that validate_not_none returns every non-None value unchanged."""
    assert validators.validate_not_none(value) is value


def test_validate_not_none_rejects_none() -> None:
    """Test that validate_not_none rejects None."""
    with pytest.raises(TypeError) as exc_info:
        validators.validate_not_none(None, name="organism")

    assert str(exc_info.value) == (
        "organism must be not None; received None of type NoneType."
    )


@pytest.mark.parametrize("value", [True, False])
def test_validate_bool_accepts_bools(value: bool) -> None:
    """Test that validate_bool accepts exact Boolean values."""
    assert validators.validate_bool(value) is value


@pytest.mark.parametrize("value", [0, 1, 0.0, 1.0, "True", None])
def test_validate_bool_rejects_non_bools(value: object) -> None:
    """Test that validate_bool rejects values that are not exact bools."""
    with pytest.raises(TypeError) as exc_info:
        validators.validate_bool(value, name="is_alive")

    assert str(exc_info.value) == (
        f"is_alive must be a bool; received {value!r} of type {type(value).__name__}."
    )


@pytest.mark.parametrize("value", [0, 1, -1, 100])
def test_validate_int_accepts_ints(value: int) -> None:
    """Test that validate_int accepts exact integers."""
    assert validators.validate_int(value) is value


@pytest.mark.parametrize(
    "value",
    [True, False, 1.0, -1.0, "1", None, float("inf"), float("nan")],
)
def test_validate_int_rejects_non_ints(value: object) -> None:
    """Test that validate_int rejects values that are not exact ints."""
    with pytest.raises(TypeError) as exc_info:
        validators.validate_int(value, name="age")

    assert str(exc_info.value) == (
        f"age must be an int; received {value!r} of type {type(value).__name__}."
    )


def test_validate_int_rejects_int_subclass() -> None:
    """Test that validate_int requires the exact built-in int type."""

    class IntSubclass(int):
        pass

    value = IntSubclass(1)

    with pytest.raises(TypeError) as exc_info:
        validators.validate_int(value)

    assert str(exc_info.value) == (
        "value must be an int; received 1 of type IntSubclass."
    )


@pytest.mark.parametrize(
    "value",
    [0.0, 1.0, -1.5, float("inf"), float("-inf"), float("nan")],
)
def test_validate_float_accepts_exact_floats(value: float) -> None:
    """Test that validate_float accepts all exact built-in floats."""
    result = validators.validate_float(value)

    assert result is value

    if math.isnan(value):
        assert math.isnan(result)


@pytest.mark.parametrize("value", [True, False, 0, 1, "1.0", None])
def test_validate_float_rejects_non_floats(value: object) -> None:
    """Test that validate_float rejects values that are not exact floats."""
    with pytest.raises(TypeError) as exc_info:
        validators.validate_float(value, name="energy")

    assert str(exc_info.value) == (
        f"energy must be a float; received {value!r} of type {type(value).__name__}."
    )


@pytest.mark.parametrize(
    "value",
    [
        0,
        -5,
        10,
        0.0,
        -5.5,
        10.25,
        float("inf"),
        float("-inf"),
        float("nan"),
    ],
)
def test_validate_number_accepts_ints_and_floats(value: int | float) -> None:
    """Test that validate_number accepts exact ints and floats."""
    assert validators.validate_number(value) is value


@pytest.mark.parametrize("value", [True, False, "1", None, [], ()])
def test_validate_number_rejects_other_types(value: object) -> None:
    """Test that validate_number rejects non-int and non-float values."""
    with pytest.raises(TypeError) as exc_info:
        validators.validate_number(value, name="delta")

    assert str(exc_info.value) == (
        f"delta must be a number; received {value!r} of type {type(value).__name__}."
    )


@pytest.mark.parametrize("value", ["", "hello", "aging"])
def test_validate_str_accepts_strings(value: str) -> None:
    """Test that validate_str accepts exact strings."""
    assert validators.validate_str(value) is value


@pytest.mark.parametrize("value", [1, 1.0, True, None, [], ()])
def test_validate_str_rejects_non_strings(value: object) -> None:
    """Test that validate_str rejects values that are not exact strings."""
    with pytest.raises(TypeError) as exc_info:
        validators.validate_str(value, name="stage")

    assert str(exc_info.value) == (
        f"stage must be a string; received {value!r} of type {type(value).__name__}."
    )


@pytest.mark.parametrize("value", [[], [1], ["a", 1]])
def test_validate_list_accepts_lists(value: list) -> None:
    """Test that validate_list accepts exact lists."""
    assert validators.validate_list(value) is value


@pytest.mark.parametrize("value", [(), set(), "list", None, 1])
def test_validate_list_rejects_non_lists(value: object) -> None:
    """Test that validate_list rejects values that are not exact lists."""
    with pytest.raises(TypeError) as exc_info:
        validators.validate_list(value, name="organisms")

    assert str(exc_info.value) == (
        f"organisms must be a list; received {value!r} of type {type(value).__name__}."
    )


@pytest.mark.parametrize("value", [(), (1,), ("a", 1)])
def test_validate_tuple_accepts_tuples(value: tuple) -> None:
    """Test that validate_tuple accepts exact tuples."""
    assert validators.validate_tuple(value) is value


@pytest.mark.parametrize("value", [[], set(), "tuple", None, 1])
def test_validate_tuple_rejects_non_tuples(value: object) -> None:
    """Test that validate_tuple rejects values that are not exact tuples."""
    with pytest.raises(TypeError) as exc_info:
        validators.validate_tuple(value, name="position")

    assert str(exc_info.value) == (
        f"position must be a tuple; received {value!r} of type {type(value).__name__}."
    )


@pytest.mark.parametrize("value", [set(), {1}, {"a", 1}])
def test_validate_set_accepts_sets(value: set) -> None:
    """Test that validate_set accepts exact sets."""
    assert validators.validate_set(value) is value


@pytest.mark.parametrize("value", [[], (), "set", None, 1])
def test_validate_set_rejects_non_sets(value: object) -> None:
    """Test that validate_set rejects values that are not exact sets."""
    with pytest.raises(TypeError) as exc_info:
        validators.validate_set(value, name="ids")

    assert str(exc_info.value) == (
        f"ids must be a set; received {value!r} of type {type(value).__name__}."
    )


# Value comparison validators


@pytest.mark.parametrize(
    ("validator", "value", "bound"),
    [
        (validators.validate_lt, 4, 5),
        (validators.validate_lt, 4.5, 5.0),
        (validators.validate_le, 5, 5),
        (validators.validate_le, 4.5, 5.0),
        (validators.validate_gt, 6, 5),
        (validators.validate_gt, 5.5, 5.0),
        (validators.validate_ge, 5, 5),
        (validators.validate_ge, 5.5, 5.0),
    ],
)
def test_comparison_validators_accept_valid_values(
    validator,
    value: int | float,
    bound: int | float,
) -> None:
    """Test that comparison validators return valid values unchanged."""
    assert validator(value=value, bound=bound) is value


@pytest.mark.parametrize(
    ("validator", "value", "bound", "requirement"),
    [
        (validators.validate_lt, 5, 5, "less than 5"),
        (validators.validate_le, 6, 5, "less than or equal to 5"),
        (validators.validate_gt, 5, 5, "greater than 5"),
        (validators.validate_ge, 4, 5, "greater than or equal to 5"),
    ],
)
def test_comparison_validators_reject_invalid_values(
    validator,
    value: int | float,
    bound: int | float,
    requirement: str,
) -> None:
    """Test boundary failures and exact comparison error messages."""
    with pytest.raises(ValueError) as exc_info:
        validator(value=value, bound=bound, name="amount")

    assert str(exc_info.value) == (f"amount must be {requirement}; received {value!r}.")


# Type and value comparison validators


@pytest.mark.parametrize(
    ("validator", "value", "bound"),
    [
        (validators.validate_number_lt, 4, 5),
        (validators.validate_number_lt, 4.5, 5),
        (validators.validate_number_le, 5, 5.0),
        (validators.validate_number_gt, 6.0, 5),
        (validators.validate_number_ge, 5, 5.0),
        (validators.validate_int_lt, 4, 5),
        (validators.validate_int_le, 5, 5),
        (validators.validate_int_gt, 6, 5),
        (validators.validate_int_ge, 5, 5),
        (validators.validate_float_lt, 4.0, 5.0),
        (validators.validate_float_le, 5.0, 5.0),
        (validators.validate_float_gt, 6.0, 5.0),
        (validators.validate_float_ge, 5.0, 5.0),
    ],
)
def test_typed_comparison_validators_accept_valid_values(
    validator,
    value: object,
    bound: object,
) -> None:
    """Test that typed comparison validators accept valid inputs."""
    assert validator(value=value, bound=bound) is value


@pytest.mark.parametrize(
    ("validator", "value", "bound", "requirement"),
    [
        (validators.validate_number_lt, 5, 5, "less than 5"),
        (validators.validate_number_le, 6, 5, "less than or equal to 5"),
        (validators.validate_number_gt, 5, 5, "greater than 5"),
        (validators.validate_number_ge, 4, 5, "greater than or equal to 5"),
        (validators.validate_int_lt, 5, 5, "less than 5"),
        (validators.validate_int_le, 6, 5, "less than or equal to 5"),
        (validators.validate_int_gt, 5, 5, "greater than 5"),
        (validators.validate_int_ge, 4, 5, "greater than or equal to 5"),
        (validators.validate_float_lt, 5.0, 5.0, "less than 5.0"),
        (validators.validate_float_le, 6.0, 5.0, "less than or equal to 5.0"),
        (validators.validate_float_gt, 5.0, 5.0, "greater than 5.0"),
        (validators.validate_float_ge, 4.0, 5.0, "greater than or equal to 5.0"),
    ],
)
def test_typed_comparison_validators_reject_invalid_values(
    validator,
    value: object,
    bound: object,
    requirement: str,
) -> None:
    """Test that typed comparison validators enforce their comparison."""
    with pytest.raises(ValueError) as exc_info:
        validator(value=value, bound=bound, name="field")

    assert str(exc_info.value) == (f"field must be {requirement}; received {value!r}.")


@pytest.mark.parametrize(
    ("validator", "invalid_value", "bound", "requirement"),
    [
        (validators.validate_number_lt, "4", 5, "a number"),
        (validators.validate_number_le, True, 5, "a number"),
        (validators.validate_number_gt, None, 5, "a number"),
        (validators.validate_number_ge, [], 5, "a number"),
        (validators.validate_int_lt, 4.0, 5, "an int"),
        (validators.validate_int_le, True, 5, "an int"),
        (validators.validate_int_gt, "4", 5, "an int"),
        (validators.validate_int_ge, None, 5, "an int"),
        (validators.validate_float_lt, 4, 5.0, "a float"),
        (validators.validate_float_le, True, 5.0, "a float"),
        (validators.validate_float_gt, "4.0", 5.0, "a float"),
        (validators.validate_float_ge, None, 5.0, "a float"),
    ],
)
def test_typed_comparison_validators_reject_invalid_value_types(
    validator,
    invalid_value: object,
    bound: object,
    requirement: str,
) -> None:
    """Test that typed comparison validators validate the value type."""
    with pytest.raises(TypeError) as exc_info:
        validator(value=invalid_value, bound=bound, name="field")

    assert str(exc_info.value) == (
        f"field must be {requirement}; received {invalid_value!r} "
        f"of type {type(invalid_value).__name__}."
    )


@pytest.mark.parametrize(
    ("validator", "value", "invalid_bound", "requirement"),
    [
        (validators.validate_number_lt, 1, "5", "a number"),
        (validators.validate_number_le, 1, True, "a number"),
        (validators.validate_number_gt, 10, None, "a number"),
        (validators.validate_number_ge, 10, [], "a number"),
        (validators.validate_int_lt, 1, 5.0, "an int"),
        (validators.validate_int_le, 1, True, "an int"),
        (validators.validate_int_gt, 10, "5", "an int"),
        (validators.validate_int_ge, 10, None, "an int"),
        (validators.validate_float_lt, 1.0, 5, "a float"),
        (validators.validate_float_le, 1.0, True, "a float"),
        (validators.validate_float_gt, 10.0, "5.0", "a float"),
        (validators.validate_float_ge, 10.0, None, "a float"),
    ],
)
def test_typed_comparison_validators_reject_invalid_bound_types(
    validator,
    value: object,
    invalid_bound: object,
    requirement: str,
) -> None:
    """Test that typed comparison validators validate the bound type."""
    with pytest.raises(TypeError) as exc_info:
        validator(value=value, bound=invalid_bound)

    assert str(exc_info.value) == (
        f"bound must be {requirement}; received {invalid_bound!r} "
        f"of type {type(invalid_bound).__name__}."
    )


class ExampleItem:
    """Represent an item used for container-validator tests."""


class ExampleItemChild(ExampleItem):
    """Represent a subclass used for container-validator tests."""


# Container item-type validators


@pytest.mark.parametrize(
    ("validator", "value"),
    [
        (
            validators.validate_list_item_type,
            [ExampleItem(), ExampleItem()],
        ),
        (
            validators.validate_tuple_item_type,
            (ExampleItem(), ExampleItem()),
        ),
        (
            validators.validate_set_item_type,
            {ExampleItem(), ExampleItem()},
        ),
    ],
)
def test_item_type_validators_accept_valid_items(
    validator,
    value: object,
) -> None:
    """Test that item-type validators accept containers of the required type."""
    result = validator(
        value=value,
        item_type=ExampleItem,
    )

    assert result is value


@pytest.mark.parametrize(
    ("validator", "value"),
    [
        (
            validators.validate_list_item_type,
            [ExampleItemChild()],
        ),
        (
            validators.validate_tuple_item_type,
            (ExampleItemChild(),),
        ),
        (
            validators.validate_set_item_type,
            {ExampleItemChild()},
        ),
    ],
)
def test_item_type_validators_accept_subclasses(
    validator,
    value: object,
) -> None:
    """Test that item-type validators accept subclasses of the item type."""
    result = validator(
        value=value,
        item_type=ExampleItem,
    )

    assert result is value


@pytest.mark.parametrize(
    ("validator", "value"),
    [
        (validators.validate_list_item_type, []),
        (validators.validate_tuple_item_type, ()),
        (validators.validate_set_item_type, set()),
    ],
)
def test_item_type_validators_accept_empty_containers(
    validator,
    value: object,
) -> None:
    """Test that item-type validators accept empty containers."""
    result = validator(
        value=value,
        item_type=ExampleItem,
    )

    assert result is value


@pytest.mark.parametrize(
    ("validator", "value", "invalid_item", "index"),
    [
        (
            validators.validate_list_item_type,
            [ExampleItem(), "bad"],
            "bad",
            1,
        ),
        (
            validators.validate_tuple_item_type,
            (ExampleItem(), "bad"),
            "bad",
            1,
        ),
    ],
)
def test_sequence_item_type_validators_reject_invalid_items(
    validator,
    value: object,
    invalid_item: object,
    index: int,
) -> None:
    """Test that list and tuple validators identify the invalid item."""
    with pytest.raises(TypeError) as exc_info:
        validator(
            value=value,
            item_type=ExampleItem,
            name="items",
        )

    assert str(exc_info.value) == (
        f"items[{index}] must be an instance of ExampleItem; "
        f"received {invalid_item!r} of type "
        f"{type(invalid_item).__name__}."
    )


def test_validate_set_item_type_rejects_invalid_item() -> None:
    """Test that validate_set_item_type rejects an invalid set item."""
    invalid_item = "bad"
    value = {invalid_item}

    with pytest.raises(TypeError) as exc_info:
        validators.validate_set_item_type(
            value=value,
            item_type=ExampleItem,
            name="items",
        )

    assert str(exc_info.value) == (
        "items[0] must be an instance of ExampleItem; received 'bad' of type str."
    )


@pytest.mark.parametrize(
    ("validator", "value", "requirement"),
    [
        (
            validators.validate_list_item_type,
            (ExampleItem(),),
            "a list",
        ),
        (
            validators.validate_tuple_item_type,
            [ExampleItem()],
            "a tuple",
        ),
        (
            validators.validate_set_item_type,
            [ExampleItem()],
            "a set",
        ),
    ],
)
def test_item_type_validators_reject_wrong_container_type(
    validator,
    value: object,
    requirement: str,
) -> None:
    """Test that item-type validators require the correct container type."""
    with pytest.raises(TypeError) as exc_info:
        validator(
            value=value,
            item_type=ExampleItem,
            name="items",
        )

    assert str(exc_info.value) == (
        f"items must be {requirement}; received {value!r} "
        f"of type {type(value).__name__}."
    )


# Dictionary validators


def test_validate_dict_accepts_dict() -> None:
    """Test that validate_dict accepts a dictionary."""
    value = {"a": 1}

    result = validators.validate_dict(value=value)

    assert result is value


def test_validate_dict_accepts_empty_dict() -> None:
    """Test that validate_dict accepts an empty dictionary."""
    value = {}

    result = validators.validate_dict(value=value)

    assert result is value


@pytest.mark.parametrize(
    "value",
    [
        pytest.param([], id="list"),
        pytest.param((), id="tuple"),
        pytest.param(set(), id="set"),
        pytest.param("dict", id="string"),
        pytest.param(1, id="int"),
        pytest.param(None, id="none"),
    ],
)
def test_validate_dict_rejects_non_dict(value: object) -> None:
    """Test that validate_dict rejects non-dictionary values."""
    with pytest.raises(TypeError) as exc_info:
        validators.validate_dict(
            value=value,
            name="items",
        )

    assert str(exc_info.value) == (
        f"items must be a dict; received {value!r} of type {type(value).__name__}."
    )


def test_validate_dict_key_item_type_accepts_valid_dict() -> None:
    """Test valid dictionary key and value types."""
    value = {
        0: ExampleItem(),
        1: ExampleItem(),
    }

    result = validators.validate_dict_key_item_type(
        value=value,
        key_type=int,
        item_type=ExampleItem,
    )

    assert result is value


def test_validate_dict_key_item_type_accepts_empty_dict() -> None:
    """Test that an empty dictionary is valid."""
    value = {}

    result = validators.validate_dict_key_item_type(
        value=value,
        key_type=int,
        item_type=ExampleItem,
    )

    assert result is value


def test_validate_dict_key_item_type_accepts_value_subclass() -> None:
    """Test that dictionary values may be subclasses of the required type."""
    value = {
        0: ExampleItemChild(),
    }

    result = validators.validate_dict_key_item_type(
        value=value,
        key_type=int,
        item_type=ExampleItem,
    )

    assert result is value


def test_validate_dict_key_item_type_rejects_wrong_container_type() -> None:
    """Test that the value itself must be a dictionary."""
    value = [(0, ExampleItem())]

    with pytest.raises(TypeError) as exc_info:
        validators.validate_dict_key_item_type(
            value=value,
            key_type=int,
            item_type=ExampleItem,
            name="items",
        )

    assert str(exc_info.value) == (
        f"items must be a dict; received {value!r} of type list."
    )


@pytest.mark.parametrize(
    "invalid_key",
    [
        pytest.param("0", id="string"),
        pytest.param(1.0, id="float"),
        pytest.param(True, id="bool"),
        pytest.param(None, id="none"),
    ],
)
def test_validate_dict_key_item_type_rejects_wrong_key_type(
    invalid_key: object,
) -> None:
    """Test that dictionary keys must have the exact required type."""
    value = {
        invalid_key: ExampleItem(),
    }

    with pytest.raises(TypeError) as exc_info:
        validators.validate_dict_key_item_type(
            value=value,
            key_type=int,
            item_type=ExampleItem,
            name="items",
        )

    assert str(exc_info.value) == (
        f"items key must be an exact int; received {invalid_key!r} "
        f"of type {type(invalid_key).__name__}."
    )


@pytest.mark.parametrize(
    "invalid_value",
    [
        pytest.param("bad", id="string"),
        pytest.param(1, id="int"),
        pytest.param(None, id="none"),
    ],
)
def test_validate_dict_key_item_type_rejects_wrong_item_type(
    invalid_value: object,
) -> None:
    """Test that dictionary values must have the required type."""
    value = {
        7: invalid_value,
    }

    with pytest.raises(TypeError) as exc_info:
        validators.validate_dict_key_item_type(
            value=value,
            key_type=int,
            item_type=ExampleItem,
            name="items",
        )

    assert str(exc_info.value) == (
        f"items[7] must be an instance of ExampleItem; "
        f"received {invalid_value!r} of type "
        f"{type(invalid_value).__name__}."
    )


def test_validate_dict_key_item_type_identifies_invalid_key() -> None:
    """Test that a key error identifies the dictionary key."""
    value = {
        0: ExampleItem(),
        "bad": ExampleItem(),
    }

    with pytest.raises(TypeError) as exc_info:
        validators.validate_dict_key_item_type(
            value=value,
            key_type=int,
            item_type=ExampleItem,
            name="items",
        )

    assert str(exc_info.value) == (
        "items key must be an exact int; received 'bad' of type str."
    )


def test_validate_dict_key_item_type_identifies_invalid_value_key() -> None:
    """Test that a value error identifies its dictionary key."""
    value = {
        0: ExampleItem(),
        5: "bad",
    }

    with pytest.raises(TypeError) as exc_info:
        validators.validate_dict_key_item_type(
            value=value,
            key_type=int,
            item_type=ExampleItem,
            name="items",
        )

    assert str(exc_info.value) == (
        "items[5] must be an instance of ExampleItem; received 'bad' of type str."
    )
