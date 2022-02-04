MAIN = """
from pydantic import BaseModel as PydanticBaseModel
from pydantic.main import ModelMetaclass
from typing import List, Optional, _GenericAlias
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


def Skip(_type):
    if (
        isinstance(_type, ModelMetaclass) or
        isinstance(_type, type) or
        isinstance(_type, _GenericAlias) or
        isinstance(_type, EnumMeta)
    ):
        return _type
    else:
        raise ValidationError("argument must be valid type")


class AdvancedBaseModel(BaseModel):
    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)
        cls_def: ast.ClassDef = ast.parse(
            textwrap.dedent(inspect.getsource(self.__class__))
        ).body[0]
        ann_assign_list = filter(lambda x: isinstance(x, ast.AnnAssign), cls_def.body)
        for ann_assign in ann_assign_list:
            if isinstance(ann_assign.annotation, ast.Call):
                func_name_obj: ast.Name = ann_assign.annotation.func
                field_name_obj: ast.Name = ann_assign.target
                if func_name_obj.id == "Skip":
                    field_name = field_name_obj.id
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
    a: Optional[Skip(Optional[str])]        # fail TCS100
    b: List[Skip(Optional[int])]            # fail TCS100
    c: Skip(Optional[Skip(Optional[str])])  # fail TCS100, TCS101
"""

INVALID_TYPE = """
class M(AdvancedBaseModel):
    a: Skip(abc)                            # fail         TCS102
    b: Skip([])                             # fail TCS101, TCS102
    c: Skip(())                             # fail TCS101, TCS102
    d: Skip()                               # fail TCS101, TCS102
    e: Skip(Skip(Optional[str]))            # fail TCS101, TCS102
"""


MISSING_OPTIONAL = """
class M(AdvancedBaseModel):
    a: Skip(List[str])                      # fail TCS102
    b: Skip(Union[str, int])                # fail TCS102
    c: Skip(Optional)                       # fail TCS102
"""
