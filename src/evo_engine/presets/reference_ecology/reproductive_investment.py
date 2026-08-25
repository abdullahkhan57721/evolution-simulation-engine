"""Reference-ecology configuration for mating-type reproductive investment."""

from __future__ import annotations

import attrs

from evo_engine.validation import attrs_validators


@attrs.frozen(slots=True, kw_only=True)
class ReferenceMatingTypeInvestmentScales:
    """Configure asymmetric parental-investment scaling in the reference ecology.

    The reference mating types remain neutral labels, but they can carry
    different reproductive energetic burdens. Both scales multiply each
    parent's heritable ``offspring_energy`` value. The defaults preserve the
    founder pair's historical total investment: a base value of four becomes
    six energy units for ``type_a`` and two for ``type_b``, totaling eight.

    Attributes:
        denominator: Positive denominator shared by both rational scales.
        type_a_numerator: Nonnegative numerator applied to ``type_a`` parents.
        type_b_numerator: Nonnegative numerator applied to ``type_b`` parents.
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
