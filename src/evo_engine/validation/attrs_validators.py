"""Attrs-compatible runtime validators for data types and values.

This module wraps the validators from `validators` for use with attrs fields.
Validation error messages identify fields by their class-qualified names in the format
"ClassName.field_name".
"""

from collections.abc import Callable

import attrs

from evo_engine.validation import validators

_AttrsValidator = Callable[[object, attrs.Attribute, object], None]


def _get_qualified_name(
    instance: object,
    attribute: attrs.Attribute,
) -> str:
    "Return the class-qualified name of an attrs attribute."
    return f"{type(instance).__name__}.{attribute.name}"


# Type validators


def validate_not_none(
    instance: object, attribute: attrs.Attribute, value: object
) -> None:
    """Validate that an attrs attribute is not None."""
    if value is not None:
        return

    qualified_name = _get_qualified_name(instance=instance, attribute=attribute)
    validators.validate_not_none(value=value, name=qualified_name)


def validate_bool(instance: object, attribute: attrs.Attribute, value: object) -> None:
    """Validate that an attrs attribute is a bool."""
    if type(value) is bool:
        return

    qualified_name = _get_qualified_name(instance=instance, attribute=attribute)
    validators.validate_bool(value=value, name=qualified_name)


def validate_int(instance: object, attribute: attrs.Attribute, value: object) -> None:
    """Validate that an attrs attribute is an int."""
    if type(value) is int:
        return

    qualified_name = _get_qualified_name(instance=instance, attribute=attribute)
    validators.validate_int(value=value, name=qualified_name)


def validate_float(instance: object, attribute: attrs.Attribute, value: object) -> None:
    """Validate that an attrs attribute is a float."""
    if type(value) is float:
        return

    qualified_name = _get_qualified_name(instance=instance, attribute=attribute)
    validators.validate_float(value=value, name=qualified_name)


def validate_number(
    instance: object, attribute: attrs.Attribute, value: object
) -> None:
    """Validate that an attrs attribute is a number."""
    if type(value) is int or type(value) is float:
        return

    qualified_name = _get_qualified_name(instance=instance, attribute=attribute)
    validators.validate_number(value=value, name=qualified_name)


def validate_str(instance: object, attribute: attrs.Attribute, value: object) -> None:
    """Validate that an attrs attribute is a string."""
    if type(value) is str:
        return

    qualified_name = _get_qualified_name(instance=instance, attribute=attribute)
    validators.validate_str(value=value, name=qualified_name)


def validate_list(instance: object, attribute: attrs.Attribute, value: object) -> None:
    """Validate that an attrs attribute is a list."""
    if type(value) is list:
        return

    qualified_name = _get_qualified_name(instance=instance, attribute=attribute)
    validators.validate_list(value=value, name=qualified_name)


def validate_list_item_type(item_type: type) -> _AttrsValidator:
    """Validate that an attrs attribute is a list and its items are of item_type"""

    def validator(instance: object, attribute: attrs.Attribute, value: object) -> None:
        if type(value) is list and all(isinstance(item, item_type) for item in value):
            return

        qualified_name = _get_qualified_name(instance=instance, attribute=attribute)
        validators.validate_list_item_type(
            value=value, item_type=item_type, name=qualified_name
        )

    return validator


def validate_tuple(instance: object, attribute: attrs.Attribute, value: object) -> None:
    """Validate that an attrs attribute is a tuple."""
    if type(value) is tuple:
        return

    qualified_name = _get_qualified_name(instance=instance, attribute=attribute)
    validators.validate_tuple(value=value, name=qualified_name)


def validate_tuple_item_type(item_type: type) -> _AttrsValidator:
    """Validate that an attrs attribute is a tuple and its items are of item_type"""

    def validator(instance: object, attribute: attrs.Attribute, value: object) -> None:
        if type(value) is tuple and all(isinstance(item, item_type) for item in value):
            return

        qualified_name = _get_qualified_name(instance=instance, attribute=attribute)
        validators.validate_tuple_item_type(
            value=value, item_type=item_type, name=qualified_name
        )

    return validator


def validate_set(instance: object, attribute: attrs.Attribute, value: object) -> None:
    """Validate that an attrs attribute is a set."""
    if type(value) is set:
        return

    qualified_name = _get_qualified_name(instance=instance, attribute=attribute)
    validators.validate_set(value=value, name=qualified_name)


def validate_set_item_type(item_type: type) -> _AttrsValidator:
    """Validate that an attrs attribute is a set and its items are of item_type"""

    def validator(instance: object, attribute: attrs.Attribute, value: object) -> None:
        if type(value) is set and all(isinstance(item, item_type) for item in value):
            return

        qualified_name = _get_qualified_name(instance=instance, attribute=attribute)
        validators.validate_set_item_type(
            value=value, item_type=item_type, name=qualified_name
        )

    return validator


def validate_dict(instance: object, attribute: attrs.Attribute, value: object) -> None:
    """Validate that an attrs attribute is a dict."""
    if type(value) is dict:
        return

    qualified_name = _get_qualified_name(instance=instance, attribute=attribute)
    validators.validate_dict(value=value, name=qualified_name)


def validate_dict_key_item_type(key_type: type, item_type: type) -> _AttrsValidator:
    """Validate that an attrs attribute is a dict and its keys are of key_type and
    its items are of item_type."""

    def validator(instance: object, attribute: attrs.Attribute, value: object) -> None:
        if type(value) is dict and all(
            type(key) is key_type and isinstance(item, item_type)
            for key, item in value.items()
        ):
            return

        qualified_name = _get_qualified_name(instance=instance, attribute=attribute)
        validators.validate_dict_key_item_type(
            value=value, key_type=key_type, item_type=item_type, name=qualified_name
        )

    return validator


# Type and value comparison validators


def validate_number_lt(bound: object) -> _AttrsValidator:
    """Return an attrs validator that validates the value is a number
    and is less than the numerical bound."""
    validated_bound = validators.validate_number(value=bound, name="bound")

    def validator(instance: object, attribute: attrs.Attribute, value: object) -> None:
        if type(value) is int and value < validated_bound:
            return
        if type(value) is float and value < validated_bound:
            return

        qualified_name = _get_qualified_name(instance=instance, attribute=attribute)
        validators.validate_number_lt(
            value=value, bound=validated_bound, name=qualified_name
        )

    return validator


def validate_number_le(bound: object) -> _AttrsValidator:
    """Return an attrs validator that validates the value is a number
    and is less than or equal to the numerical bound."""
    validated_bound = validators.validate_number(value=bound, name="bound")

    def validator(instance: object, attribute: attrs.Attribute, value: object) -> None:
        if type(value) is int and value <= validated_bound:
            return
        if type(value) is float and value <= validated_bound:
            return

        qualified_name = _get_qualified_name(instance=instance, attribute=attribute)
        validators.validate_number_le(
            value=value, bound=validated_bound, name=qualified_name
        )

    return validator


def validate_number_gt(bound: object) -> _AttrsValidator:
    """Return an attrs validator that validates the value is a number
    and is greater than the numerical bound."""
    validated_bound = validators.validate_number(value=bound, name="bound")

    def validator(instance: object, attribute: attrs.Attribute, value: object) -> None:
        if type(value) is int and value > validated_bound:
            return
        if type(value) is float and value > validated_bound:
            return

        qualified_name = _get_qualified_name(instance=instance, attribute=attribute)
        validators.validate_number_gt(
            value=value, bound=validated_bound, name=qualified_name
        )

    return validator


def validate_number_ge(bound: object) -> _AttrsValidator:
    """Return an attrs validator that validates the value is a number
    and is greater than or equal to the numerical bound."""
    validated_bound = validators.validate_number(value=bound, name="bound")

    def validator(instance: object, attribute: attrs.Attribute, value: object) -> None:
        if type(value) is int and value >= validated_bound:
            return
        if type(value) is float and value >= validated_bound:
            return

        qualified_name = _get_qualified_name(instance=instance, attribute=attribute)
        validators.validate_number_ge(
            value=value, bound=validated_bound, name=qualified_name
        )

    return validator


def validate_int_lt(bound: object) -> _AttrsValidator:
    """Return an attrs validator that validates the value is an int
    and is less than the numerical bound."""
    validated_bound = validators.validate_int(value=bound, name="bound")

    def validator(instance: object, attribute: attrs.Attribute, value: object) -> None:
        if type(value) is int and value < validated_bound:
            return

        qualified_name = _get_qualified_name(instance=instance, attribute=attribute)
        validators.validate_int_lt(
            value=value, bound=validated_bound, name=qualified_name
        )

    return validator


def validate_int_le(bound: object) -> _AttrsValidator:
    """Return an attrs validator that validates the value is an int
    and is less than or equal to the numerical bound."""
    validated_bound = validators.validate_int(value=bound, name="bound")

    def validator(instance: object, attribute: attrs.Attribute, value: object) -> None:
        if type(value) is int and value <= validated_bound:
            return

        qualified_name = _get_qualified_name(instance=instance, attribute=attribute)
        validators.validate_int_le(
            value=value, bound=validated_bound, name=qualified_name
        )

    return validator


def validate_int_gt(bound: object) -> _AttrsValidator:
    """Return an attrs validator that validates the value is an int
    and is greater than the numerical bound."""
    validated_bound = validators.validate_int(value=bound, name="bound")

    def validator(instance: object, attribute: attrs.Attribute, value: object) -> None:
        if type(value) is int and value > validated_bound:
            return

        qualified_name = _get_qualified_name(instance=instance, attribute=attribute)
        validators.validate_int_gt(
            value=value, bound=validated_bound, name=qualified_name
        )

    return validator


def validate_int_ge(bound: object) -> _AttrsValidator:
    """Return an attrs validator that validates the value is a int
    and is greater than or equal to the numerical bound."""
    validated_bound = validators.validate_int(value=bound, name="bound")

    def validator(instance: object, attribute: attrs.Attribute, value: object) -> None:
        if type(value) is int and value >= validated_bound:
            return

        qualified_name = _get_qualified_name(instance=instance, attribute=attribute)
        validators.validate_int_ge(
            value=value, bound=validated_bound, name=qualified_name
        )

    return validator


def validate_float_lt(bound: object) -> _AttrsValidator:
    """Return an attrs validator that validates the value is a float
    and is less than the numerical bound."""
    validated_bound = validators.validate_float(value=bound, name="bound")

    def validator(instance: object, attribute: attrs.Attribute, value: object) -> None:
        if type(value) is float and value < validated_bound:
            return

        qualified_name = _get_qualified_name(instance=instance, attribute=attribute)
        validators.validate_float_lt(
            value=value, bound=validated_bound, name=qualified_name
        )

    return validator


def validate_float_le(bound: object) -> _AttrsValidator:
    """Return an attrs validator that validates the value is a float
    and is less than or equal to the numerical bound."""
    validated_bound = validators.validate_float(value=bound, name="bound")

    def validator(instance: object, attribute: attrs.Attribute, value: object) -> None:
        if type(value) is float and value <= validated_bound:
            return

        qualified_name = _get_qualified_name(instance=instance, attribute=attribute)
        validators.validate_float_le(
            value=value, bound=validated_bound, name=qualified_name
        )

    return validator


def validate_float_gt(bound: object) -> _AttrsValidator:
    """Return an attrs validator that validates the value is a float
    and is greater than the numerical bound."""
    validated_bound = validators.validate_float(value=bound, name="bound")

    def validator(instance: object, attribute: attrs.Attribute, value: object) -> None:
        if type(value) is float and value > validated_bound:
            return

        qualified_name = _get_qualified_name(instance=instance, attribute=attribute)
        validators.validate_float_gt(
            value=value, bound=validated_bound, name=qualified_name
        )

    return validator


def validate_float_ge(bound: object) -> _AttrsValidator:
    """Return an attrs validator that validates the value is a float
    and is greater than or equal to the numerical bound."""
    validated_bound = validators.validate_float(value=bound, name="bound")

    def validator(instance: object, attribute: attrs.Attribute, value: object) -> None:
        if type(value) is float and value >= validated_bound:
            return

        qualified_name = _get_qualified_name(instance=instance, attribute=attribute)
        validators.validate_float_ge(
            value=value, bound=validated_bound, name=qualified_name
        )

    return validator


def validate_int_in_range(
    lower: int,
    upper: int,
) -> _AttrsValidator:
    """Return an attrs validator for an integer within a range.

    Args:
        lower: Inclusive lower bound.
        upper: Inclusive upper bound.

    Returns:
        Attrs-compatible validator.
    """

    def _validator(
        instance: object,
        attribute: attrs.Attribute,
        value: object,
    ) -> None:
        if (
            type(lower) is int
            and type(upper) is int
            and lower <= upper
            and type(value) is int
            and lower <= value <= upper
        ):
            return

        validators.validate_int_in_range(
            value,
            lower=lower,
            upper=upper,
            name=attribute.name,
        )

    return _validator


def validate_number_in_range(
    lower: int | float,
    upper: int | float,
) -> _AttrsValidator:
    """Return an attrs validator for a number within a range.

    Args:
        lower: Inclusive lower bound.
        upper: Inclusive upper bound.

    Returns:
        Attrs-compatible validator.
    """

    def _validator(
        instance: object,
        attribute: attrs.Attribute,
        value: object,
    ) -> None:
        bounds_are_numbers = (type(lower) is int or type(lower) is float) and (
            type(upper) is int or type(upper) is float
        )
        if bounds_are_numbers and lower <= upper:
            if type(value) is int and lower <= value <= upper:
                return
            if type(value) is float and lower <= value <= upper:
                return

        validators.validate_number_in_range(
            value,
            lower=lower,
            upper=upper,
            name=attribute.name,
        )

    return _validator


def validate_float_in_range(
    lower: int | float,
    upper: int | float,
) -> _AttrsValidator:
    """Return an attrs validator for a float within a range.

    Args:
        lower: Inclusive lower bound.
        upper: Inclusive upper bound.

    Returns:
        Attrs-compatible validator.
    """

    def _validator(
        instance: object,
        attribute: attrs.Attribute,
        value: object,
    ) -> None:
        if (
            type(lower) is float
            and type(upper) is float
            and lower <= upper
            and type(value) is float
            and lower <= value <= upper
        ):
            return

        validators.validate_float_in_range(
            value,
            lower=lower,
            upper=upper,
            name=attribute.name,
        )

    return _validator
