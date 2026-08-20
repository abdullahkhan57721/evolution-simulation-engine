"""Runtime validators for data types and values.

Validator list
-------------------

### Type validators

- ``validate_not_none``
- ``validate_bool``
- ``validate_int``
- ``validate_float``
- ``validate_number``
- ``validate_str``
- ``validate_list``
- ``validate_tuple``
- ``validate_set``
- ``validate_list_item_type``
- ``validate_tuple_item_type``
- ``validate_set_item_type``

### Value comparison validators

- ``validate_lt``
- ``validate_le``
- ``validate_gt``
- ``validate_ge``

### Type AND value comparison validators
Number (int|float):
- ``validate_number_lt``
- ``validate_number_le``
- ``validate_number_gt``
- ``validate_number_ge``
- ``validate_number_in_range``

Integer:
- ``validate_int_lt``
- ``validate_int_le``
- ``validate_int_gt``
- ``validate_int_ge``
- ``validate_int_in_range``


Float:
- ``validate_float_lt``
- ``validate_float_le``
- ``validate_float_gt``
- ``validate_float_ge``
- ``validate_float_in_range``
"""

from __future__ import annotations

from typing import TypeVar

N = TypeVar("N", int, float)
T = TypeVar("T")


def _type_error(value: object, name: str, requirement: str) -> TypeError:
    return TypeError(
        f"{name} must be {requirement}; received {value!r} of type {type(value).__name__}."
    )


def _value_error(value: object, name: str, requirement: str) -> ValueError:
    return ValueError(f"{name} must be {requirement}; received {value!r}.")


# Type validators


def validate_not_none(value: object, name: str = "value") -> object:
    """Validate that the value is not None."""
    if value is None:
        raise _type_error(value=value, name=name, requirement="not None")
    return value


def validate_bool(value: object, name: str = "value") -> bool:
    """Validate that the value is a Boolean."""
    if type(value) is bool:
        return value
    raise _type_error(value=value, name=name, requirement="a bool")


def validate_int(value: object, name: str = "value") -> int:
    """Validate that the value is an integer."""
    if type(value) is int:
        return value
    raise _type_error(value=value, name=name, requirement="an int")


def validate_float(value: object, name: str = "value") -> float:
    """Validate that the value is a float."""
    if type(value) is float:
        return value
    raise _type_error(value=value, name=name, requirement="a float")


def validate_number(value: object, name: str = "value") -> int | float:
    """Validate that the value is a number."""

    if type(value) is int:
        return value
    if type(value) is float:
        return value
    raise _type_error(value=value, name=name, requirement="a number")


def validate_str(value: object, name: str = "value") -> str:
    """Validate that the value is a string."""
    if type(value) is str:
        return value
    raise _type_error(value=value, name=name, requirement="a string")


def validate_list(value: object, name: str = "value") -> list:
    """Validate that the value is a list."""
    if type(value) is list:
        return value
    raise _type_error(value=value, name=name, requirement="a list")


def validate_list_item_type(
    value: object, item_type: type, name: str = "value"
) -> list:
    """Validate that the value is a list and the items in it are of type item_type."""
    validated_list = validate_list(value=value, name=name)

    for index, item in enumerate(validated_list):
        if not isinstance(item, item_type):
            qualified_name = f"{name}[{index}]"
            raise _type_error(
                value=item,
                name=qualified_name,
                requirement=f"an instance of {item_type.__name__}",
            )

    return validated_list


def validate_tuple(value: object, name: str = "value") -> tuple:
    """Validate that the value is a tuple."""
    if type(value) is tuple:
        return value
    raise _type_error(value=value, name=name, requirement="a tuple")


def validate_tuple_item_type(
    value: object, item_type: type, name: str = "value"
) -> tuple:
    """Validate that the value is a tuple and the items in it are of type item_type."""
    validated_tuple = validate_tuple(value=value, name=name)

    for index, item in enumerate(validated_tuple):
        if not isinstance(item, item_type):
            qualified_name = f"{name}[{index}]"
            raise _type_error(
                value=item,
                name=qualified_name,
                requirement=f"an instance of {item_type.__name__}",
            )

    return validated_tuple


def validate_set(value: object, name: str = "value") -> set:
    """Validate that the value is a set."""
    if type(value) is set:
        return value
    raise _type_error(value=value, name=name, requirement="a set")


def validate_set_item_type(value: object, item_type: type, name: str = "value") -> set:
    """Validate that the value is a set and the items in it are of type item_type."""
    validated_set = validate_set(value=value, name=name)

    for index, item in enumerate(validated_set):
        if not isinstance(item, item_type):
            qualified_name = f"{name}[{index}]"
            raise _type_error(
                value=item,
                name=qualified_name,
                requirement=f"an instance of {item_type.__name__}",
            )

    return validated_set


def validate_dict(value: object, name: str = "value") -> dict:
    """Validate that the value is a dictionary."""
    if type(value) is dict:
        return value
    raise _type_error(value=value, name=name, requirement="a dict")


def validate_dict_key_item_type(
    value: object, key_type: type, item_type: type, name: str = "value"
) -> dict:
    """Validate that the value is a dict and the keys are of key_type and
    the items in it are of item_type."""
    validated_dict = validate_dict(value=value, name=name)

    for key, item in validated_dict.items():
        if type(key) is not key_type:
            qualified_name = f"{name} key"
            raise _type_error(
                value=key,
                name=qualified_name,
                requirement=f"an exact {key_type.__name__}",
            )

        if not isinstance(item, item_type):
            qualified_name = f"{name}[{key!r}]"
            raise _type_error(
                value=item,
                name=qualified_name,
                requirement=f"an instance of {item_type.__name__}",
            )

    return validated_dict


# Value comparison validators


def validate_lt(value: N, bound: N, name: str = "value") -> N:
    """Validate that the numerical value is less than the numerical bound."""
    if value < bound:
        return value
    raise _value_error(value=value, name=name, requirement=f"less than {bound}")


def validate_le(value: N, bound: N, name: str = "value") -> N:
    """Validate that the numerical value is less than or equal to the numerical bound."""
    if value <= bound:
        return value
    raise _value_error(
        value=value, name=name, requirement=f"less than or equal to {bound}"
    )


def validate_gt(value: N, bound: N, name: str = "value") -> N:
    """Validate that the numerical value is greater than the numerical bound."""
    if value > bound:
        return value
    raise _value_error(value=value, name=name, requirement=f"greater than {bound}")


def validate_ge(value: N, bound: N, name: str = "value") -> N:
    """Validate that the numerical value is greater than or equal to the numerical bound."""
    if value >= bound:
        return value
    raise _value_error(
        value=value, name=name, requirement=f"greater than or equal to {bound}"
    )


# Type and value comparison validators


def validate_number_lt(
    value: object, bound: object, name: str = "value"
) -> int | float:
    """Validate that the value is a number and is less than the numerical bound."""
    number_value = validate_number(value=value, name=name)
    number_bound = validate_number(value=bound, name="bound")
    return validate_lt(value=number_value, bound=number_bound, name=name)


def validate_number_le(
    value: object, bound: object, name: str = "value"
) -> int | float:
    """Validate that the value is a number and is less than or equal to the numerical bound."""
    number_value = validate_number(value=value, name=name)
    number_bound = validate_number(value=bound, name="bound")
    return validate_le(value=number_value, bound=number_bound, name=name)


def validate_number_gt(
    value: object, bound: object, name: str = "value"
) -> int | float:
    """Validate that the value is a number and is greater than the numerical bound."""
    number_value = validate_number(value=value, name=name)
    number_bound = validate_number(value=bound, name="bound")
    return validate_gt(value=number_value, bound=number_bound, name=name)


def validate_number_ge(
    value: object, bound: object, name: str = "value"
) -> int | float:
    """Validate that the value is a number and is greater than or equal to the numerical bound."""
    number_value = validate_number(value=value, name=name)
    number_bound = validate_number(value=bound, name="bound")
    return validate_ge(value=number_value, bound=number_bound, name=name)


def validate_number_in_range(
    value: object, lower: int | float, upper: int | float, name: str = "value"
) -> None:
    """Validate that an number is within an inclusive range."""
    validate_number(lower, name="lower")
    validate_number(upper, name="upper")

    if lower > upper:
        raise ValueError(
            f"lower must be less than or equal to upper; "
            f"received lower={lower} and upper={upper}."
        )

    validate_number_ge(value, bound=lower, name=name)
    validate_number_le(value, bound=upper, name=name)


def validate_int_lt(value: object, bound: object, name: str = "value") -> int:
    """Validate that the value is an int and is less than the numerical bound."""
    int_value = validate_int(value=value, name=name)
    int_bound = validate_int(value=bound, name="bound")
    return validate_lt(value=int_value, bound=int_bound, name=name)


def validate_int_le(value: object, bound: object, name: str = "value") -> int:
    """Validate that the value is an int and is less than or equal to the numerical bound."""
    int_value = validate_int(value=value, name=name)
    int_bound = validate_int(value=bound, name="bound")
    return validate_le(value=int_value, bound=int_bound, name=name)


def validate_int_gt(value: object, bound: object, name: str = "value") -> int:
    """Validate that the value is an int and is greater than the numerical bound."""
    int_value = validate_int(value=value, name=name)
    int_bound = validate_int(value=bound, name="bound")
    return validate_gt(value=int_value, bound=int_bound, name=name)


def validate_int_ge(value: object, bound: object, name: str = "value") -> int:
    """Validate that the value is an int and is greater than or equal to the numerical bound."""
    int_value = validate_int(value=value, name=name)
    int_bound = validate_int(value=bound, name="bound")
    return validate_ge(value=int_value, bound=int_bound, name=name)


def validate_int_in_range(
    value: object, lower: int, upper: int, name: str = "value"
) -> None:
    """Validate that an integer is within an inclusive range."""
    validate_int(lower, name="lower")
    validate_int(upper, name="upper")

    if lower > upper:
        raise ValueError(
            f"lower must be less than or equal to upper; "
            f"received lower={lower} and upper={upper}."
        )

    validate_int_ge(value, bound=lower, name=name)
    validate_int_le(value, bound=upper, name=name)


def validate_float_lt(value: object, bound: object, name: str = "value") -> float:
    """Validate that the value is a float and is less than the numerical bound."""
    float_value = validate_float(value=value, name=name)
    float_bound = validate_float(value=bound, name="bound")
    return validate_lt(value=float_value, bound=float_bound, name=name)


def validate_float_le(value: object, bound: object, name: str = "value") -> float:
    """Validate that the value is a float and is less than or equal to the numerical bound."""
    float_value = validate_float(value=value, name=name)
    float_bound = validate_float(value=bound, name="bound")
    return validate_le(value=float_value, bound=float_bound, name=name)


def validate_float_gt(value: object, bound: object, name: str = "value") -> float:
    """Validate that the value is a float and is greater than the numerical bound."""
    float_value = validate_float(value=value, name=name)
    float_bound = validate_float(value=bound, name="bound")
    return validate_gt(value=float_value, bound=float_bound, name=name)


def validate_float_ge(value: object, bound: object, name: str = "value") -> float:
    """Validate that the value is a float and is greater than or equal to the numerical bound."""
    float_value = validate_float(value=value, name=name)
    float_bound = validate_float(value=bound, name="bound")
    return validate_ge(value=float_value, bound=float_bound, name=name)


def validate_float_in_range(
    value: object, lower: float, upper: float, name: str = "value"
) -> None:
    """Validate that a float is within an inclusive range."""
    validate_float(lower, name="lower")
    validate_float(upper, name="upper")

    if lower > upper:
        raise ValueError(
            f"lower must be less than or equal to upper; "
            f"received lower={lower} and upper={upper}."
        )

    validate_float_ge(value, bound=lower, name=name)
    validate_float_le(value, bound=upper, name=name)
