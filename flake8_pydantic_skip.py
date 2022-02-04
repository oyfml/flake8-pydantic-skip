import ast
import importlib.metadata
from typing import NamedTuple, List, Union, Iterator, Tuple


class Flake8ASTErrorInfo(NamedTuple):
    line_number: int
    offset: int
    msg: str
    cls: type  # unused currently, but required


SPECIAL_MODEL_NAME = "AdvancedBaseModel"
SKIP_FUNC_NAME = "Skip"


class TypeWrappingNotAllowed:
    msg = "TCS100 {field_name} in {model_name}: Skip must not type wrapped"

    @classmethod
    def check(cls, node: ast.ClassDef, errors: List[Flake8ASTErrorInfo]) -> None:
        """
        Checks if Skip is incorrectly wrapped by a type
        """
        if SPECIAL_MODEL_NAME in set(b.id for b in node.bases):
            for child in node.body:
                if isinstance(child, ast.AnnAssign):
                    cls.inspect(
                        child.annotation,
                        errors,
                        msg_names=(child.target.id, node.name),
                        first_depth=True,
                    )

    @classmethod
    def inspect(
        cls,
        node: Union[ast.Name, ast.Subscript, ast.Call],
        errors: List[Flake8ASTErrorInfo],
        msg_names: Tuple[str, str],
        first_depth: bool = False,
    ) -> None:
        """
        Recursively inspects child nodes to flag nested Skip beyond first depth
        """
        if isinstance(node, ast.Name):
            return
        elif isinstance(node, ast.Subscript):
            cls.inspect(node.slice.value, errors, msg_names)
        elif isinstance(node, ast.Tuple):
            for element in node.elts:
                cls.inspect(element, errors, msg_names)
        elif (
            isinstance(node, ast.Call)
            and node.func.id == SKIP_FUNC_NAME
            and not first_depth
        ):
            err = Flake8ASTErrorInfo(
                node.lineno,
                node.col_offset,
                cls.msg.format(field_name=msg_names[0], model_name=msg_names[1]),
                cls,
            )
            errors.append(err)
            cls.inspect(node.args[0], errors, msg_names)


class InvalidTypeNotAllowed:
    msg = "TCS101 {field_name} in {model_name}: Invalid type argument in Skip definition"

    @classmethod
    def check(cls, node: ast.ClassDef, errors: List[Flake8ASTErrorInfo]) -> None:
        """
        Checks for field assignment with invalid type in Skip parenthesis
        """
        if SPECIAL_MODEL_NAME in set(b.id for b in node.bases):
            for child in node.body:
                if (
                    isinstance(child, ast.AnnAssign)
                    and isinstance(child.annotation, ast.Call)
                    and child.annotation.func.id == SKIP_FUNC_NAME
                ):
                    if len(child.annotation.args) > 0:
                        cls.inspect(
                            child.annotation.args[0],
                            errors,
                            msg_names=(child.target.id, node.name),
                        )
                    else:
                        err = Flake8ASTErrorInfo(
                            child.annotation.lineno,
                            child.annotation.col_offset,
                            cls.msg.format(
                                field_name=child.target.id, model_name=node.name
                            ),
                            cls,
                        )
                        errors.append(err)

    @classmethod
    def inspect(
        cls,
        node: Union[ast.Name, ast.Subscript, ast.Call],
        errors: List[Flake8ASTErrorInfo],
        msg_names: Tuple[str, str],
    ) -> None:
        """
        Recursively inspects child nodes to flag nested Skip beyond first depth
        """
        if isinstance(node, ast.Name):
            # does not check if name is valid py variable / class / enum
            return
        elif isinstance(node, ast.Subscript):
            cls.inspect(node.slice.value, errors, msg_names)
        elif isinstance(node, ast.Tuple):
            if len(node.elts) > 0:
                for element in node.elts:
                    cls.inspect(element, errors, msg_names)
            # fail empty tuples
            else:
                err = Flake8ASTErrorInfo(
                    node.lineno,
                    node.col_offset,
                    cls.msg.format(field_name=msg_names[0], model_name=msg_names[1]),
                    cls,
                )
                errors.append(err)
        # invalid type
        else:
            err = Flake8ASTErrorInfo(
                node.lineno,
                node.col_offset,
                cls.msg.format(field_name=msg_names[0], model_name=msg_names[1]),
                cls,
            )
            errors.append(err)
            # note: do not need to catch Skip(str = None) or Skip(Optional[]) since syntax error


class MissingOptionalNotAllowed:
    msg = (
        "TCS102 {field_name} in {model_name}: Skip expects Optional type as argument"
    )

    @classmethod
    def check(cls, node: ast.ClassDef, errors: List[Flake8ASTErrorInfo]) -> None:
        """
        Checks use of Skip must wrap Optional
        """
        if SPECIAL_MODEL_NAME in set(b.id for b in node.bases):
            for child in node.body:
                if (
                    isinstance(child, ast.AnnAssign)
                    and isinstance(child.annotation, ast.Call)
                    and child.annotation.func.id == SKIP_FUNC_NAME
                ):
                    # Optional
                    if (
                        len(child.annotation.args) > 0
                        and isinstance(child.annotation.args[0], ast.Subscript)
                        and child.annotation.args[0].value.id == "Optional"
                    ):
                        continue
                    # Union
                    elif (
                        len(child.annotation.args) > 0
                        and isinstance(child.annotation.args[0], ast.Subscript)
                        and child.annotation.args[0].value.id == "Union"
                        and isinstance(child.annotation.args[0].slice.value, ast.Tuple)
                    ):
                        elements = child.annotation.args[0].slice.value.elts
                        constants = filter(
                            lambda x: isinstance(x, ast.Constant), elements
                        )
                        if any(c.value is None for c in constants):
                            continue

                    err = Flake8ASTErrorInfo(
                        child.annotation.lineno,
                        child.annotation.col_offset,
                        cls.msg.format(
                            field_name=child.target.id, model_name=node.name
                        ),
                        cls,
                    )
                    errors.append(err)


class Visitor(ast.NodeVisitor):
    def __init__(self):
        self.errors: List[Flake8ASTErrorInfo] = []

    def visit_ClassDef(self, node: ast.ClassDef):
        TypeWrappingNotAllowed.check(node, self.errors)
        InvalidTypeNotAllowed.check(node, self.errors)
        MissingOptionalNotAllowed.check(node, self.errors)
        self.generic_visit(node)  # continue visiting child nodes


class Plugin:
    name = __name__
    version = importlib.metadata.version(__name__)

    def __init__(self, tree: ast.AST):
        self._tree = tree

    def run(self) -> Iterator[Flake8ASTErrorInfo]:
        visitor = Visitor()
        visitor.visit(self._tree)
        yield from visitor.errors
