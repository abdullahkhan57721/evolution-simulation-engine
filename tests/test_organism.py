from _pytest.python import pytest_generate_tests
import pytest

from evo_engine.organism import Organism


@pytest.mark.parametrize("negative_id", [-1, -3, -3.2])
def test_organism_rejects_negative_id_value(negative_id):
    with pytest.raises(ValueError):
        Organism(id=negative_id)


@pytest.mark.parametrize("non_int_id", ["abc", True, 3.2, 0.0, None])
def test_organism_rejects_non_int_id_type(non_int_id):
    with pytest.raises(TypeError):
        Organism(id=non_int_id)


@pytest.mark.parametrize("negative_age", [-1, -3, -3.2])
def test_organism_rejects_negative_age_value(negative_age):
    with pytest.raises(ValueError):
        Organism(id=0, age=negative_age)


@pytest.mark.parametrize("non_int_age", ["abc", True, 3.2, 0.0, None])
def test_organism_rejects_non_int_age_type(non_int_age):
    with pytest.raises(TypeError):
        Organism(id=0, age=non_int_age)


@pytest.mark.parametrize("non_bool_value", [0, 2, 2.3, -4.3, "abc", None])
def test_organism_rejects_non_bool_is_alive(non_bool_value):
    with pytest.raises(TypeError):
        Organism(id=0, is_alive=non_bool_value)


@pytest.mark.parametrize("positive_int_id", [0, 5, 23])
def test_organism_accepts_positive_int_id(positive_int_id):
    organism = Organism(id=positive_int_id)

    assert organism.id == positive_int_id


@pytest.mark.parametrize("positive_int_age", [0, 5, 23])
def test_organism_accepts_positive_int_age(positive_int_age):
    organism = Organism(id=5, age=positive_int_age)

    assert organism.age == positive_int_age


@pytest.mark.parametrize("bool_value", [True, False])
def test_organism_accepts_bool_is_alive(bool_value):
    organism = Organism(id=5, is_alive=bool_value)

    assert organism.is_alive is bool_value




    

