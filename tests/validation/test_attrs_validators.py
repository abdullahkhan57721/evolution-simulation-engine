"""Tests for the attrs-compatible runtime validators."""

from collections.abc import Callable

import attrs
import pytest

from evo_engine.validation import attrs_validators

# Type validators


@pytest.mark.parametrize(
    ("validator", "valid_value"),
    [
        (attrs_validators.validate_not_none, 1),
        (attrs_validators.validate_bool, True),
        (attrs_validators.validate_int, 1),
        (attrs_validators.validate_float, 1.0),
        (attrs_validators.validate_number, 1.5),
        (attrs_validators.validate_list, []),
        (attrs_validators.validate_tuple, ()),
        (attrs_validators.validate_set, set()),
    ],
)
def test_attrs_type_validators_accept_valid_values(
    validator: Callable,
    valid_value: object,
) -> None:
    """Test that attrs type validators accept valid field values."""

    @attrs.define
    class Model:
        value: object = attrs.field(validator=validator)

    model = Model(value=valid_value)

    assert model.value is valid_value


@pytest.mark.parametrize(
    ("validator", "invalid_value", "requirement"),
    [
        (attrs_validators.validate_not_none, None, "not None"),
        (attrs_validators.validate_bool, 1, "a bool"),
        (attrs_validators.validate_int, 1.0, "an int"),
        (attrs_validators.validate_float, 1, "a float"),
        (attrs_validators.validate_number, True, "a number"),
        (attrs_validators.validate_list, (), "a list"),
        (attrs_validators.validate_tuple, [], "a tuple"),
        (attrs_validators.validate_set, [], "a set"),
    ],
)
def test_attrs_type_validators_use_qualified_name_on_construction(
    validator: Callable,
    invalid_value: object,
    requirement: str,
) -> None:
    """Test qualified error names when attrs constructs an invalid object."""

    @attrs.define
    class Model:
        value: object = attrs.field(validator=validator)

    with pytest.raises(TypeError) as exc_info:
        Model(value=invalid_value)

    assert str(exc_info.value) == (
        f"Model.value must be {requirement}; received {invalid_value!r} "
        f"of type {type(invalid_value).__name__}."
    )


@pytest.mark.parametrize(
    ("validator", "valid_value", "invalid_value", "requirement"),
    [
        (attrs_validators.validate_not_none, 1, None, "not None"),
        (attrs_validators.validate_bool, True, 1, "a bool"),
        (attrs_validators.validate_int, 1, 1.0, "an int"),
        (attrs_validators.validate_float, 1.0, 1, "a float"),
        (attrs_validators.validate_number, 1, True, "a number"),
        (attrs_validators.validate_list, [], (), "a list"),
        (attrs_validators.validate_tuple, (), [], "a tuple"),
        (attrs_validators.validate_set, set(), [], "a set"),
    ],
)
def test_attrs_type_validators_run_on_assignment(
    validator: Callable,
    valid_value: object,
    invalid_value: object,
    requirement: str,
) -> None:
    """Test that attrs validators run again when a mutable field is assigned."""

    @attrs.define
    class Model:
        value: object = attrs.field(validator=validator)

    model = Model(value=valid_value)

    with pytest.raises(TypeError) as exc_info:
        model.value = invalid_value

    assert str(exc_info.value) == (
        f"Model.value must be {requirement}; received {invalid_value!r} "
        f"of type {type(invalid_value).__name__}."
    )


# Type and value comparison validator factories


@pytest.mark.parametrize(
    ("factory", "bound", "valid_value"),
    [
        (attrs_validators.validate_number_lt, 5, 4),
        (attrs_validators.validate_number_le, 5, 5.0),
        (attrs_validators.validate_number_gt, 5, 6.0),
        (attrs_validators.validate_number_ge, 5, 5),
        (attrs_validators.validate_int_lt, 5, 4),
        (attrs_validators.validate_int_le, 5, 5),
        (attrs_validators.validate_int_gt, 5, 6),
        (attrs_validators.validate_int_ge, 5, 5),
        (attrs_validators.validate_float_lt, 5.0, 4.0),
        (attrs_validators.validate_float_le, 5.0, 5.0),
        (attrs_validators.validate_float_gt, 5.0, 6.0),
        (attrs_validators.validate_float_ge, 5.0, 5.0),
    ],
)
def test_attrs_comparison_factories_accept_valid_values(
    factory: Callable,
    bound: object,
    valid_value: object,
) -> None:
    """Test validators returned by the attrs comparison factories."""

    @attrs.define
    class Model:
        value: object = attrs.field(validator=factory(bound))

    model = Model(value=valid_value)

    assert model.value is valid_value


@pytest.mark.parametrize(
    ("factory", "bound", "invalid_value", "requirement"),
    [
        (attrs_validators.validate_number_lt, 5, 5, "less than 5"),
        (attrs_validators.validate_number_le, 5, 6, "less than or equal to 5"),
        (attrs_validators.validate_number_gt, 5, 5, "greater than 5"),
        (attrs_validators.validate_number_ge, 5, 4, "greater than or equal to 5"),
        (attrs_validators.validate_int_lt, 5, 5, "less than 5"),
        (attrs_validators.validate_int_le, 5, 6, "less than or equal to 5"),
        (attrs_validators.validate_int_gt, 5, 5, "greater than 5"),
        (attrs_validators.validate_int_ge, 5, 4, "greater than or equal to 5"),
        (attrs_validators.validate_float_lt, 5.0, 5.0, "less than 5.0"),
        (
            attrs_validators.validate_float_le,
            5.0,
            6.0,
            "less than or equal to 5.0",
        ),
        (attrs_validators.validate_float_gt, 5.0, 5.0, "greater than 5.0"),
        (
            attrs_validators.validate_float_ge,
            5.0,
            4.0,
            "greater than or equal to 5.0",
        ),
    ],
)
def test_attrs_comparison_validators_use_qualified_name(
    factory: Callable,
    bound: object,
    invalid_value: object,
    requirement: str,
) -> None:
    """Test qualified names for failed attrs comparison validation."""

    @attrs.define
    class Model:
        value: object = attrs.field(validator=factory(bound))

    with pytest.raises(ValueError) as exc_info:
        Model(value=invalid_value)

    assert str(exc_info.value) == (
        f"Model.value must be {requirement}; received {invalid_value!r}."
    )


@pytest.mark.parametrize(
    ("factory", "bound", "valid_value", "invalid_value", "requirement"),
    [
        (attrs_validators.validate_number_lt, 5, 4, 5, "less than 5"),
        (attrs_validators.validate_number_le, 5, 5, 6, "less than or equal to 5"),
        (attrs_validators.validate_number_gt, 5, 6, 5, "greater than 5"),
        (attrs_validators.validate_number_ge, 5, 5, 4, "greater than or equal to 5"),
        (attrs_validators.validate_int_lt, 5, 4, 5, "less than 5"),
        (attrs_validators.validate_int_le, 5, 5, 6, "less than or equal to 5"),
        (attrs_validators.validate_int_gt, 5, 6, 5, "greater than 5"),
        (attrs_validators.validate_int_ge, 5, 5, 4, "greater than or equal to 5"),
        (attrs_validators.validate_float_lt, 5.0, 4.0, 5.0, "less than 5.0"),
        (
            attrs_validators.validate_float_le,
            5.0,
            5.0,
            6.0,
            "less than or equal to 5.0",
        ),
        (attrs_validators.validate_float_gt, 5.0, 6.0, 5.0, "greater than 5.0"),
        (
            attrs_validators.validate_float_ge,
            5.0,
            5.0,
            4.0,
            "greater than or equal to 5.0",
        ),
    ],
)
def test_attrs_comparison_validators_run_on_assignment(
    factory: Callable,
    bound: object,
    valid_value: object,
    invalid_value: object,
    requirement: str,
) -> None:
    """Test comparison validators when attrs fields are reassigned."""

    @attrs.define
    class Model:
        value: object = attrs.field(validator=factory(bound))

    model = Model(value=valid_value)

    with pytest.raises(ValueError) as exc_info:
        model.value = invalid_value

    assert str(exc_info.value) == (
        f"Model.value must be {requirement}; received {invalid_value!r}."
    )


@pytest.mark.parametrize(
    ("factory", "invalid_bound", "requirement"),
    [
        (attrs_validators.validate_number_lt, "5", "a number"),
        (attrs_validators.validate_number_le, True, "a number"),
        (attrs_validators.validate_number_gt, None, "a number"),
        (attrs_validators.validate_number_ge, [], "a number"),
        (attrs_validators.validate_int_lt, 5.0, "an int"),
        (attrs_validators.validate_int_le, True, "an int"),
        (attrs_validators.validate_int_gt, "5", "an int"),
        (attrs_validators.validate_int_ge, None, "an int"),
        (attrs_validators.validate_float_lt, 5, "a float"),
        (attrs_validators.validate_float_le, True, "a float"),
        (attrs_validators.validate_float_gt, "5.0", "a float"),
        (attrs_validators.validate_float_ge, None, "a float"),
    ],
)
def test_attrs_comparison_factories_reject_invalid_bounds_immediately(
    factory: Callable,
    invalid_bound: object,
    requirement: str,
) -> None:
    """Test that invalid factory bounds fail before an attrs class uses them."""
    with pytest.raises(TypeError) as exc_info:
        factory(invalid_bound)

    assert str(exc_info.value) == (
        f"bound must be {requirement}; received {invalid_bound!r} "
        f"of type {type(invalid_bound).__name__}."
    )


@pytest.mark.parametrize(
    ("factory", "bound", "invalid_value", "requirement"),
    [
        (attrs_validators.validate_number_lt, 5, True, "a number"),
        (attrs_validators.validate_number_le, 5, "4", "a number"),
        (attrs_validators.validate_number_gt, 5, None, "a number"),
        (attrs_validators.validate_number_ge, 5, [], "a number"),
        (attrs_validators.validate_int_lt, 5, 4.0, "an int"),
        (attrs_validators.validate_int_le, 5, True, "an int"),
        (attrs_validators.validate_int_gt, 5, "6", "an int"),
        (attrs_validators.validate_int_ge, 5, None, "an int"),
        (attrs_validators.validate_float_lt, 5.0, 4, "a float"),
        (attrs_validators.validate_float_le, 5.0, True, "a float"),
        (attrs_validators.validate_float_gt, 5.0, "6.0", "a float"),
        (attrs_validators.validate_float_ge, 5.0, None, "a float"),
    ],
)
def test_attrs_comparison_validators_reject_invalid_value_types(
    factory: Callable,
    bound: object,
    invalid_value: object,
    requirement: str,
) -> None:
    """Test type checking through attrs comparison wrappers."""

    @attrs.define
    class Model:
        value: object = attrs.field(validator=factory(bound))

    with pytest.raises(TypeError) as exc_info:
        Model(value=invalid_value)

    assert str(exc_info.value) == (
        f"Model.value must be {requirement}; received {invalid_value!r} "
        f"of type {type(invalid_value).__name__}."
    )


class ExampleItem:
    """Represent an item used for attrs container-validator tests."""


class ExampleItemChild(ExampleItem):
    """Represent a subclass used for attrs container-validator tests."""


@pytest.mark.parametrize(
    ("factory", "valid_value"),
    [
        (
            attrs_validators.validate_list_item_type,
            [ExampleItem(), ExampleItem()],
        ),
        (
            attrs_validators.validate_tuple_item_type,
            (ExampleItem(), ExampleItem()),
        ),
        (
            attrs_validators.validate_set_item_type,
            {ExampleItem(), ExampleItem()},
        ),
    ],
)
def test_attrs_item_type_validators_accept_valid_items(
    factory,
    valid_value: object,
) -> None:
    """Test attrs item-type validators with valid containers."""

    @attrs.define
    class Model:
        items: object = attrs.field(
            validator=factory(ExampleItem),
        )

    model = Model(items=valid_value)

    assert model.items is valid_value


@pytest.mark.parametrize(
    ("factory", "valid_value"),
    [
        (
            attrs_validators.validate_list_item_type,
            [ExampleItemChild()],
        ),
        (
            attrs_validators.validate_tuple_item_type,
            (ExampleItemChild(),),
        ),
        (
            attrs_validators.validate_set_item_type,
            {ExampleItemChild()},
        ),
    ],
)
def test_attrs_item_type_validators_accept_subclasses(
    factory,
    valid_value: object,
) -> None:
    """Test attrs item-type validators accept subclasses."""

    @attrs.define
    class Model:
        items: object = attrs.field(
            validator=factory(ExampleItem),
        )

    model = Model(items=valid_value)

    assert model.items is valid_value


@pytest.mark.parametrize(
    ("factory", "invalid_value", "index"),
    [
        (
            attrs_validators.validate_list_item_type,
            [ExampleItem(), "bad"],
            1,
        ),
        (
            attrs_validators.validate_tuple_item_type,
            (ExampleItem(), "bad"),
            1,
        ),
    ],
)
def test_attrs_sequence_item_type_validators_use_qualified_name(
    factory,
    invalid_value: object,
    index: int,
) -> None:
    """Test qualified names for invalid list and tuple members."""

    @attrs.define
    class Model:
        items: object = attrs.field(
            validator=factory(ExampleItem),
        )

    with pytest.raises(TypeError) as exc_info:
        Model(items=invalid_value)

    assert str(exc_info.value) == (
        f"Model.items[{index}] must be an instance of ExampleItem; "
        "received 'bad' of type str."
    )


def test_attrs_set_item_type_validator_uses_qualified_name() -> None:
    """Test the qualified field name for an invalid set item."""

    @attrs.define
    class Model:
        items: object = attrs.field(
            validator=attrs_validators.validate_set_item_type(
                ExampleItem,
            ),
        )

    with pytest.raises(TypeError) as exc_info:
        Model(items={"bad"})

    assert str(exc_info.value) == (
        "Model.items[0] must be an instance of ExampleItem; received 'bad' of type str."
    )


@pytest.mark.parametrize(
    ("factory", "invalid_value", "requirement"),
    [
        (
            attrs_validators.validate_list_item_type,
            (ExampleItem(),),
            "a list",
        ),
        (
            attrs_validators.validate_tuple_item_type,
            [ExampleItem()],
            "a tuple",
        ),
        (
            attrs_validators.validate_set_item_type,
            [ExampleItem()],
            "a set",
        ),
    ],
)
def test_attrs_item_type_validators_reject_wrong_container_type(
    factory,
    invalid_value: object,
    requirement: str,
) -> None:
    """Test that attrs item validators require the correct container."""

    @attrs.define
    class Model:
        items: object = attrs.field(
            validator=factory(ExampleItem),
        )

    with pytest.raises(TypeError) as exc_info:
        Model(items=invalid_value)

    assert str(exc_info.value) == (
        f"Model.items must be {requirement}; "
        f"received {invalid_value!r} of type "
        f"{type(invalid_value).__name__}."
    )


@pytest.mark.parametrize(
    ("factory", "initial_value", "invalid_value"),
    [
        (
            attrs_validators.validate_list_item_type,
            [ExampleItem()],
            ["bad"],
        ),
        (
            attrs_validators.validate_tuple_item_type,
            (ExampleItem(),),
            ("bad",),
        ),
    ],
)
def test_attrs_item_type_validators_run_on_assignment(
    factory,
    initial_value: object,
    invalid_value: object,
) -> None:
    """Test that item-type validators run on field reassignment."""

    @attrs.define
    class Model:
        items: object = attrs.field(
            validator=factory(ExampleItem),
        )

    model = Model(items=initial_value)

    with pytest.raises(TypeError):
        model.items = invalid_value


def test_attrs_set_item_type_validator_runs_on_assignment() -> None:
    """Test set item-type validation on field reassignment."""

    @attrs.define
    class Model:
        items: object = attrs.field(
            validator=attrs_validators.validate_set_item_type(
                ExampleItem,
            ),
        )

    model = Model(items={ExampleItem()})

    with pytest.raises(TypeError):
        model.items = {"bad"}


# Dictionary attrs validators


def test_attrs_validate_dict_accepts_dict() -> None:
    """Test that the attrs dictionary validator accepts a dictionary."""

    @attrs.define
    class Model:
        items: object = attrs.field(
            validator=attrs_validators.validate_dict,
        )

    value = {"a": 1}

    model = Model(items=value)

    assert model.items is value


def test_attrs_validate_dict_rejects_non_dict() -> None:
    """Test that the attrs dictionary validator rejects non-dictionaries."""

    @attrs.define
    class Model:
        items: object = attrs.field(
            validator=attrs_validators.validate_dict,
        )

    value = []

    with pytest.raises(TypeError) as exc_info:
        Model(items=value)

    assert str(exc_info.value) == (
        "Model.items must be a dict; received [] of type list."
    )


def test_attrs_dict_key_item_type_accepts_valid_dict() -> None:
    """Test valid dictionary key and value types through attrs."""

    @attrs.define
    class Model:
        items: object = attrs.field(
            validator=attrs_validators.validate_dict_key_item_type(
                int,
                ExampleItem,
            ),
        )

    value = {
        0: ExampleItem(),
        1: ExampleItem(),
    }

    model = Model(items=value)

    assert model.items is value


def test_attrs_dict_key_item_type_accepts_empty_dict() -> None:
    """Test that the attrs validator accepts an empty dictionary."""

    @attrs.define
    class Model:
        items: object = attrs.field(
            validator=attrs_validators.validate_dict_key_item_type(
                int,
                ExampleItem,
            ),
        )

    value = {}

    model = Model(items=value)

    assert model.items is value


def test_attrs_dict_key_item_type_accepts_value_subclass() -> None:
    """Test that attrs dictionary values may be subclasses."""

    @attrs.define
    class Model:
        items: object = attrs.field(
            validator=attrs_validators.validate_dict_key_item_type(
                int,
                ExampleItem,
            ),
        )

    value = {
        0: ExampleItemChild(),
    }

    model = Model(items=value)

    assert model.items is value


def test_attrs_dict_key_item_type_rejects_wrong_container() -> None:
    """Test that the attrs validator requires a dictionary."""

    @attrs.define
    class Model:
        items: object = attrs.field(
            validator=attrs_validators.validate_dict_key_item_type(
                int,
                ExampleItem,
            ),
        )

    value = []

    with pytest.raises(TypeError) as exc_info:
        Model(items=value)

    assert str(exc_info.value) == (
        "Model.items must be a dict; received [] of type list."
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
def test_attrs_dict_key_item_type_rejects_wrong_key_type(
    invalid_key: object,
) -> None:
    """Test that attrs dictionary keys require the exact type."""

    @attrs.define
    class Model:
        items: object = attrs.field(
            validator=attrs_validators.validate_dict_key_item_type(
                int,
                ExampleItem,
            ),
        )

    value = {
        invalid_key: ExampleItem(),
    }

    with pytest.raises(TypeError) as exc_info:
        Model(items=value)

    assert str(exc_info.value) == (
        f"Model.items key must be an exact int; "
        f"received {invalid_key!r} of type "
        f"{type(invalid_key).__name__}."
    )


@pytest.mark.parametrize(
    "invalid_value",
    [
        pytest.param("bad", id="string"),
        pytest.param(1, id="int"),
        pytest.param(None, id="none"),
    ],
)
def test_attrs_dict_key_item_type_rejects_wrong_item_type(
    invalid_value: object,
) -> None:
    """Test that attrs dictionary values require the correct type."""

    @attrs.define
    class Model:
        items: object = attrs.field(
            validator=attrs_validators.validate_dict_key_item_type(
                int,
                ExampleItem,
            ),
        )

    value = {
        3: invalid_value,
    }

    with pytest.raises(TypeError) as exc_info:
        Model(items=value)

    assert str(exc_info.value) == (
        f"Model.items[3] must be an instance of ExampleItem; "
        f"received {invalid_value!r} of type "
        f"{type(invalid_value).__name__}."
    )


def test_attrs_dict_key_item_type_runs_on_assignment() -> None:
    """Test dictionary key/value validation on field reassignment."""

    @attrs.define
    class Model:
        items: object = attrs.field(
            validator=attrs_validators.validate_dict_key_item_type(
                int,
                ExampleItem,
            ),
        )

    model = Model(
        items={
            0: ExampleItem(),
        }
    )

    with pytest.raises(TypeError) as exc_info:
        model.items = {
            0: "bad",
        }

    assert str(exc_info.value) == (
        "Model.items[0] must be an instance of ExampleItem; received 'bad' of type str."
    )
