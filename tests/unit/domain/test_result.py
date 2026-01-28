"""
Unit tests for app/domain/result.py - Ok, Err, match_result
"""

import pytest

from app.domain.result import Ok, Err, match_result


class TestOk:

    def test_is_ok_returns_true(self):
        assert Ok(42).is_ok() is True

    def test_is_err_returns_false(self):
        assert Ok(42).is_err() is False

    def test_unwrap_returns_value(self):
        assert Ok("hello").unwrap() == "hello"

    def test_unwrap_or_returns_value_not_default(self):
        assert Ok(10).unwrap_or(99) == 10

    def test_unwrap_err_raises(self):
        with pytest.raises(ValueError, match="Called unwrap_err on Ok"):
            Ok(42).unwrap_err()

    def test_map_transforms_value(self):
        result = Ok(5).map(lambda x: x * 2)
        assert isinstance(result, Ok)
        assert result.unwrap() == 10

    def test_map_err_returns_self(self):
        original = Ok(5)
        mapped = original.map_err(lambda e: str(e))
        assert isinstance(mapped, Ok)
        assert mapped.unwrap() == 5

    def test_ok_with_none_value(self):
        result = Ok(None)
        assert result.is_ok() is True
        assert result.unwrap() is None

    def test_ok_frozen_dataclass(self):
        result = Ok(42)
        with pytest.raises(AttributeError):
            result.value = 99

    def test_ok_equality(self):
        assert Ok(42) == Ok(42)
        assert Ok(42) != Ok(99)


class TestErr:

    def test_is_ok_returns_false(self):
        assert Err("fail").is_ok() is False

    def test_is_err_returns_true(self):
        assert Err("fail").is_err() is True

    def test_unwrap_raises(self):
        with pytest.raises(ValueError, match="Called unwrap on Err"):
            Err("oops").unwrap()

    def test_unwrap_or_returns_default(self):
        assert Err("fail").unwrap_or(42) == 42

    def test_unwrap_err_returns_error(self):
        assert Err("oops").unwrap_err() == "oops"

    def test_map_returns_self(self):
        original = Err("fail")
        mapped = original.map(lambda x: x * 2)
        assert isinstance(mapped, Err)
        assert mapped.unwrap_err() == "fail"

    def test_map_err_transforms_error(self):
        result = Err("fail").map_err(lambda e: e.upper())
        assert isinstance(result, Err)
        assert result.unwrap_err() == "FAIL"

    def test_err_frozen_dataclass(self):
        result = Err("fail")
        with pytest.raises(AttributeError):
            result.error = "new"

    def test_err_equality(self):
        assert Err("a") == Err("a")
        assert Err("a") != Err("b")


class TestMatchResult:

    def test_match_ok(self):
        result = match_result(Ok(10), ok_fn=lambda v: v + 1, err_fn=lambda e: -1)
        assert result == 11

    def test_match_err(self):
        result = match_result(Err("bad"), ok_fn=lambda v: v + 1, err_fn=lambda e: e.upper())
        assert result == "BAD"
