import ast
import importlib.metadata
from typing import Any, Generator, List, NamedTuple, Tuple, Type


class Flake8ASTErrorInfo(NamedTuple):
    line_number: int
    offset: int
    msg: str


SPECIAL_MODEL_NAME = "SkippableBaseModel"
SKIP_FUNC_NAME = "Skip"


class TypeWrappingNotAllowed:
    def __init__(self, model_name: str, errors: List[Flake8ASTErrorInfo]) -> None:
        self.model_name = model_name
        self.errors = errors
        self.msg = "SKP100 {field_name} in {model_name}: Skip must not type wrapped"

    def check(self, node: ast.AnnAssign) -> None:
        """
        Checks if Skip is incorrectly wrapped by a type
        """
        if not isinstance(node.target, ast.Name):
            raise TypeError("node.target must be ast.Name")

        self.inspect(
            node.annotation,
            msg_names=(node.target.id, self.model_name),
            first_depth=True,
        )

    def inspect(
        self,
        node: ast.expr,
        msg_names: Tuple[str, str],
        first_depth: bool = False,
    ) -> None:
        """
        Recursively inspects child nodes to flag nested Skip beyond first depth
        """
        if isinstance(node, ast.Name):
            return
        elif isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Index):
            self.inspect(node.slice.value, msg_names)
        elif isinstance(node, ast.Tuple):
            for element in node.elts:
                self.inspect(element, msg_names)
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == SKIP_FUNC_NAME
            and not first_depth
        ):
            err = Flake8ASTErrorInfo(
                node.lineno,
                node.col_offset,
                self.msg.format(field_name=msg_names[0], model_name=msg_names[1]),
            )
            self.errors.append(err)
            self.inspect(node.args[0], msg_names)


class InvalidTypeNotAllowed:
    def __init__(self, model_name: str, errors: List[Flake8ASTErrorInfo]) -> None:
        self.model_name = model_name
        self.errors = errors
        self.msg = "SKP101 {field_name} in {model_name}: Invalid type argument in Skip definition"

    def check(self, node: ast.AnnAssign) -> None:
        """
        Checks for field assignment with invalid type in Skip parenthesis
        """
        if not isinstance(node.target, ast.Name):
            raise TypeError("node.target must be ast.Name")

        if (
            isinstance(node.annotation, ast.Call)
            and isinstance(node.annotation.func, ast.Name)
            and node.annotation.func.id == SKIP_FUNC_NAME
        ):
            if len(node.annotation.args) > 0:
                self.inspect(
                    node.annotation.args[0],
                    msg_names=(node.target.id, self.model_name),
                )
            # for Skip()
            else:
                err = Flake8ASTErrorInfo(
                    node.annotation.lineno,
                    node.annotation.col_offset,
                    self.msg.format(
                        field_name=node.target.id, model_name=self.model_name
                    ),
                )
                self.errors.append(err)
        # for Skip
        elif (
            isinstance(node.annotation, ast.Name)
            and node.annotation.id == SKIP_FUNC_NAME
        ):
            err = Flake8ASTErrorInfo(
                node.annotation.lineno,
                node.annotation.col_offset,
                self.msg.format(field_name=node.target.id, model_name=self.model_name),
            )
            self.errors.append(err)

    def inspect(
        self,
        node: ast.expr,
        msg_names: Tuple[str, str],
    ) -> None:
        """
        Recursively inspects child nodes to flag nested Skip beyond first depth
        """
        if isinstance(node, ast.Name):
            if node.id == SKIP_FUNC_NAME:
                err = Flake8ASTErrorInfo(
                    node.lineno,
                    node.col_offset,
                    self.msg.format(field_name=msg_names[0], model_name=msg_names[1]),
                )
                self.errors.append(err)
            # does not check if name is valid py variable / class / enum
            # other than Skip
            return
        elif isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Index):
            self.inspect(node.slice.value, msg_names)
        elif isinstance(node, ast.Tuple):
            if len(node.elts) > 0:
                for element in node.elts:
                    self.inspect(element, msg_names)
            # fail empty tuples
            else:
                err = Flake8ASTErrorInfo(
                    node.lineno,
                    node.col_offset,
                    self.msg.format(field_name=msg_names[0], model_name=msg_names[1]),
                )
                self.errors.append(err)
        # invalid type
        else:
            err = Flake8ASTErrorInfo(
                node.lineno,
                node.col_offset,
                self.msg.format(field_name=msg_names[0], model_name=msg_names[1]),
            )
            self.errors.append(err)
            # note: do not need to catch Skip(str = None) or Skip(Optional[]) since syntax error


class MissingOptionalNotAllowed:
    def __init__(self, model_name: str, errors: List[Flake8ASTErrorInfo]) -> None:
        self.model_name = model_name
        self.errors = errors
        self.msg = "SKP102 {field_name} in {model_name}: Skip expects Optional type as argument"

    def check(self, node: ast.AnnAssign) -> None:
        """
        Checks use of Skip must wrap Optional
        """
        if not isinstance(node.target, ast.Name):
            raise TypeError("node.target must be ast.Name")

        if (
            isinstance(node.annotation, ast.Call)
            and isinstance(node.annotation.func, ast.Name)
            and node.annotation.func.id == SKIP_FUNC_NAME
        ):
            # Optional
            if (
                len(node.annotation.args) > 0
                and isinstance(node.annotation.args[0], ast.Subscript)
                and isinstance(node.annotation.args[0].value, ast.Name)
                and node.annotation.args[0].value.id == "Optional"
            ):
                return
            # Union
            elif (
                len(node.annotation.args) > 0
                and isinstance(node.annotation.args[0], ast.Subscript)
                and isinstance(node.annotation.args[0].value, ast.Name)
                and node.annotation.args[0].value.id == "Union"
                and isinstance(node.annotation.args[0].slice, ast.Index)
                and isinstance(node.annotation.args[0].slice.value, ast.Tuple)
            ):
                elements = node.annotation.args[0].slice.value.elts
                constants = [e for e in elements if isinstance(e, ast.Constant)]
                if any(c.value is None for c in constants):
                    return

            err = Flake8ASTErrorInfo(
                node.annotation.lineno,
                node.annotation.col_offset,
                self.msg.format(field_name=node.target.id, model_name=self.model_name),
            )
            self.errors.append(err)


class Visitor(ast.NodeVisitor):
    def __init__(self):
        self.errors: List[Flake8ASTErrorInfo] = []

    def visit_ClassDef(self, node: ast.ClassDef):
        if SPECIAL_MODEL_NAME in set(
            b.id for b in node.bases if isinstance(b, ast.Name)
        ):
            for child in node.body:
                if isinstance(child, ast.AnnAssign):
                    TypeWrappingNotAllowed(node.name, self.errors).check(child)
                    InvalidTypeNotAllowed(node.name, self.errors).check(child)
                    MissingOptionalNotAllowed(node.name, self.errors).check(child)
                self.generic_visit(node)  # continue visiting child nodes


class Plugin:
    name = __name__
    version = importlib.metadata.version(__name__)

    def __init__(self, tree: ast.AST):
        self._tree = tree

    def run(self) -> Generator[Tuple[int, int, str, Type[Any]], None, None]:
        visitor = Visitor()
        visitor.visit(self._tree)
        for line, col, msg in visitor.errors:
            yield line, col, msg, type(self)
