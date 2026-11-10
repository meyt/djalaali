import pytest

from djalaali import algo

pytestmark = pytest.mark.skipif(
    not algo.HAS_C_EXTENSION, reason="C extension not available"
)


def _outcome(fn, *args):
    try:
        return fn(*args)
    except algo.ErrorInvalidYear as e:
        return ("ErrorInvalidYear", e.year)
    except ValueError as e:
        return ("ValueError", str(e))


def test_to_jalaali_matches_python():
    for gy in range(1, 2700):
        for gm in range(1, 13):
            for gd in (1, 10, 20, 28):
                args = (gy, gm, gd)
                assert _outcome(algo.to_jalaali, *args) == _outcome(
                    algo._py_to_jalaali, *args
                )


def test_to_gregorian_matches_python():
    for jy in range(-70, 3190):
        for jm in range(14):
            for jd in (0, 1, 15, 29, 30, 31, 32):
                args = (jy, jm, jd)
                assert _outcome(algo.to_gregorian, *args) == _outcome(
                    algo._py_to_gregorian, *args
                )


def test_leap_and_month_length_match_python():
    for jy in range(-70, 3190):
        assert _outcome(algo.is_leap_year, jy) == _outcome(
            algo._py_is_leap_year, jy
        )
        for jm in range(14):
            assert _outcome(algo.month_length, jy, jm) == _outcome(
                algo._py_month_length, jy, jm
            )


@pytest.mark.parametrize("big", [10**13, -(10**13), 10**30, -(10**30)])
def test_huge_arguments_fall_back_to_python(big):
    for args in ((big, 1, 1), (2024, 1, big), (2024, big, 1)):
        assert _outcome(algo.to_jalaali, *args) == _outcome(
            algo._py_to_jalaali, *args
        )
    assert _outcome(algo.is_leap_year, big) == _outcome(
        algo._py_is_leap_year, big
    )
    assert _outcome(algo.month_length, 1400, big) == _outcome(
        algo._py_month_length, 1400, big
    )
    assert _outcome(algo.to_gregorian, 1400, 1, big) == _outcome(
        algo._py_to_gregorian, 1400, 1, big
    )


def test_bad_argument_types():
    with pytest.raises(TypeError):
        algo.to_jalaali("2024", 1, 1)
    with pytest.raises(TypeError):
        algo.to_jalaali(2024, 1)
