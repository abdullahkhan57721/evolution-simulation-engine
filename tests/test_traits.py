import pytest

from evo_engine.traits import TraitSet


def test_default_energy_efficiency_is_point_five():
    traits = TraitSet()

    assert traits.energy_efficiency == 0.5


def test_validate_accepts_valid_energy_efficiency():
    traits = TraitSet(energy_efficiency=0.75)

    traits.validate()


@pytest.mark.parametrize("energy_efficiency", [-0.1, 1.1])
def test_validate_rejects_energy_efficiency_outside_range(energy_efficiency):
    traits = TraitSet(energy_efficiency=energy_efficiency)

    with pytest.raises(ValueError):
        traits.validate()


def test_validate_rejects_invalid_bounds():
    traits = TraitSet(energy_efficiency=0.5)

    with pytest.raises(ValueError):
        traits.validate(min_energy_efficiency=1.0, max_energy_efficiency=0.3)


def test_copy_returns_equal_but_separate_trait_sets():
    original = TraitSet(energy_efficiency=0.6)

    copied = original.copy()

    assert copied.energy_efficiency == original.energy_efficiency
    assert copied is not original


def test_to_dict_returns_plain_dictionary():
    traits = TraitSet(energy_efficiency=0.7)

    result = traits.to_dict()

    assert result == {"energy_efficiency": 0.7}
