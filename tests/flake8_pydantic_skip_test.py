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
        "60:16: TCS100 a in M: Skip must not type wrapped",
        "61:12: TCS100 b in M: Skip must not type wrapped",
        "62:21: TCS101 c in M: Invalid type argument in Skip definition",
    }


def test_invalid_type_in_skip():
    assert results(MAIN + INVALID_TYPE) == {
        "61:12: TCS101 b in M: Invalid type argument in Skip definition",
        "62:12: TCS101 c in M: Invalid type argument in Skip definition",
        "63:7: TCS101 d in M: Invalid type argument in Skip definition",
        "64:12: TCS101 e in M: Invalid type argument in Skip definition",
        "60:7: TCS102 a in M: Skip expects Optional type as argument",
        "61:7: TCS102 b in M: Skip expects Optional type as argument",
        "62:7: TCS102 c in M: Skip expects Optional type as argument",
        "63:7: TCS102 d in M: Skip expects Optional type as argument",
        "64:7: TCS102 e in M: Skip expects Optional type as argument",
    }


def test_missing_optional_in_skip():
    assert results(MAIN + MISSING_OPTIONAL) == {
        "60:7: TCS102 a in M: Skip expects Optional type as argument",
        "61:7: TCS102 b in M: Skip expects Optional type as argument",
        "62:7: TCS102 c in M: Skip expects Optional type as argument",
    }
