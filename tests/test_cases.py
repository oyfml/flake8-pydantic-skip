MAIN = """
from pydantic import BaseModel as PydanticBaseModel
from typing import List, Optional, Union, _GenericAlias
from enum import Enum, EnumMeta

import inspect
import ast
import textwrap


class BaseModel(PydanticBaseModel):
    class Config:
        validate_assignment = True
        validate_all = True
        extra = "ignore"
        use_enum_values = True


def Skip(_type: Any, default=None):
    return _type


class AdvancedBaseModel(BaseModel):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        cls_def = [
            i
            for i in ast.parse(textwrap.dedent(inspect.getsource(self.__class__))).body
            if isinstance(i, ast.ClassDef)
        ][0]
        ann_assign_list = [i for i in cls_def.body if isinstance(i, ast.AnnAssign)]
        for ann_assign in ann_assign_list:
            if isinstance(ann_assign.annotation, ast.Call):
                func_name_obj: ast.Name = ann_assign.annotation.__getattribute__("func")
                field_name_obj: ast.Name = ann_assign.__getattribute__("target")
                if func_name_obj.id == "Skip":
                    field_name = field_name_obj.id
                    if field_name not in self.__fields_set__:
                        if len(ann_assign.annotation.keywords) > 0:
                            keyword = [
                                kw
                                for kw in ann_assign.annotation.keywords
                                if kw.arg == "default"
                            ][0]
                            self.__dict__[field_name] = keyword.value.__getattribute__(
                                "value"
                            )
                        elif len(ann_assign.annotation.args) == 2:
                            self.__dict__[field_name] = ann_assign.annotation.args[
                                -1
                            ].__getattribute__("value")
                    if (
                        not self.__fields__[field_name].required
                        and self.__dict__[field_name] is None
                    ):
                        self.__delattr__(field_name)

class E(Enum):
    ONE = "1"
    TWO = "2"
    THREE = "3"

class BM(BaseModel):
    a: str
"""
CLEAN_VANILLA = """
class M(AdvancedBaseModel):
    a: str
    b: Optional[List[str]]
    c: List[List[List[List[int]]]]
    d: E
    e: List[E]
    f: str = "123"
    g: BM
    h: Union[BM, None]
    i: BM = None
"""

CLEAN_SKIP = """
class M(AdvancedBaseModel):
    a: Skip(Optional[List[str]])
    c: Skip(Optional[List[List[List[int]]]])
    d: E
    e: List[E]
    f: str = "123"
    g: BM
    h: Optional[BM]
"""

FORBID_TYPE_WRAP = """
class M(AdvancedBaseModel):
    a: Optional[Skip(Optional[str])]        # fail SKP100
    b: List[Skip(Optional[int])]            # fail SKP100
    c: Skip(Optional[Skip(Optional[str])])  # fail SKP100, SKP101
"""

INVALID_TYPE = """
class M(AdvancedBaseModel):
    a: Skip(abc)                            # fail         SKP102
    b: Skip([])                             # fail SKP101, SKP102
    c: Skip(())                             # fail SKP101, SKP102
    d: Skip()                               # fail SKP101, SKP102
    e: Skip(Skip(Optional[str]))            # fail SKP101, SKP102
"""


MISSING_OPTIONAL = """
class M(AdvancedBaseModel):
    a: Skip(List[str])                      # fail SKP102
    b: Skip(Union[str, int])                # fail SKP102
    c: Skip(Optional)                       # fail SKP102
"""
