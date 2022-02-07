import ast
from flake8_pydantic_skip import Plugin

from .test_cases import (
    MAIN,
    CLEAN_VANILLA,
    CLEAN_SKIP,
    FORBID_TYPE_WRAP,
    INVALID_TYPE,
    MISSING_OPTIONAL,
)


def results(s):
    return {"{}:{}: {}".format(*r) for r in Plugin(ast.parse(s)).run()}


def test_clean_vanilla():
    assert results(MAIN + CLEAN_VANILLA) == set()


def test_clean_skip():
    assert results(MAIN + CLEAN_SKIP) == set()


def test_forbidden_type_wrap_in_skip():
    assert results(MAIN + FORBID_TYPE_WRAP) == {
        "67:16: SKP100 a in M: Skip must not type wrapped",
        "68:12: SKP100 b in M: Skip must not type wrapped",
        "69:21: SKP101 c in M: Invalid type argument in Skip definition",
    }


def test_invalid_type_in_skip():
    assert results(MAIN + INVALID_TYPE) == {
        "68:12: SKP101 b in M: Invalid type argument in Skip definition",
        "69:12: SKP101 c in M: Invalid type argument in Skip definition",
        "70:7: SKP101 d in M: Invalid type argument in Skip definition",
        "71:12: SKP101 e in M: Invalid type argument in Skip definition",
        "67:7: SKP102 a in M: Skip expects Optional type as argument",
        "68:7: SKP102 b in M: Skip expects Optional type as argument",
        "69:7: SKP102 c in M: Skip expects Optional type as argument",
        "70:7: SKP102 d in M: Skip expects Optional type as argument",
        "71:7: SKP102 e in M: Skip expects Optional type as argument",
    }


def test_missing_optional_in_skip():
    assert results(MAIN + MISSING_OPTIONAL) == {
        "67:7: SKP102 a in M: Skip expects Optional type as argument",
        "68:7: SKP102 b in M: Skip expects Optional type as argument",
        "69:7: SKP102 c in M: Skip expects Optional type as argument",
    }
