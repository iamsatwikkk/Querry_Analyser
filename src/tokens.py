from enum import Enum, auto
from dataclasses import dataclass


class TokenType(Enum):
    KEYWORD = auto()
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()
    OPERATOR = auto()
    COMMA = auto()
    SEMICOLON = auto()
    EOF = auto()


KEYWORDS = {"SELECT", "FROM", "WHERE", "AND", "OR"}

COMPARISON_OPERATORS = {"=", ">", "<", ">=", "<="}


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, line={self.line}, col={self.column})"
