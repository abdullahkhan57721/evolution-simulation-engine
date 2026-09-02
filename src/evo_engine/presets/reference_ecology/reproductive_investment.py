"""Reference-ecology configuration for mating-type reproductive investment."""

from __future__ import annotations

import attrs

from evo_engine.presets.reference_ecology.mating_types import REFERENCE_MATING_TYPES
from evo_engine.reproduction import (
    CharacteristicEnergyInvestment,
    MatingTypeInvestmentScale,
    MatingTypeScaledInvestment,
)
from evo_engine.validation import attrs_validators


@attrs.frozen(slots=True, kw_only=True)
class ReferenceMatingTypeInvestmentScales:
    """Configure asymmetric reproductive-investor scaling in the reference ecology.

    The reference mating types remain neutral labels, but selected investors can
    carry different reproductive energetic burdens. Both scales multiply each
    investor's realized ``offspring_energy`` characteristic. The defaults preserve
    the founder pair's historical total investment when development leaves that
    characteristic unchanged: a base value of four becomes six energy units for
    ``type_a`` and two for ``type_b``, totaling eight.

    Attributes:
        denominator: Positive denominator shared by both rational scales.
        type_a_numerator: Nonnegative numerator applied to ``type_a`` investors.
        type_b_numerator: Nonnegative numerator applied to ``type_b`` investors.
    """

    denominator: int = attrs.field(
        default=2,
        validator=attrs_validators.validate_int_gt(0),
    )
    type_a_numerator: int = attrs.field(
        default=3,
        validator=attrs_validators.validate_int_ge(0),
    )
    type_b_numerator: int = attrs.field(
        default=1,
        validator=attrs_validators.validate_int_ge(0),
    )


def build_reference_reproductive_investment(
    scales: ReferenceMatingTypeInvestmentScales,
) -> MatingTypeScaledInvestment:
    """Build the reference mating-type-scaled reproductive investment policy.

    Args:
        scales: Reference rational scale configuration.

    Returns:
        Reproductive-investment policy that scales the realized
        ``offspring_energy`` characteristic according to each selected investor's
        mating type.
    """
    type_a, type_b = REFERENCE_MATING_TYPES
    return MatingTypeScaledInvestment(
        base_investment=CharacteristicEnergyInvestment(),
        scales=(
            MatingTypeInvestmentScale(
                mating_type=type_a,
                numerator=scales.type_a_numerator,
                denominator=scales.denominator,
            ),
            MatingTypeInvestmentScale(
                mating_type=type_b,
                numerator=scales.type_b_numerator,
                denominator=scales.denominator,
            ),
        ),
    )
