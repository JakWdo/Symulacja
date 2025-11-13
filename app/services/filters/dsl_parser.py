"""
DSL Parser - parsowanie zapytań filtrujących do AST

Implementuje parser dla Domain Specific Language (DSL) do filtrowania zasobów.
Używa Shunting Yard Algorithm do konwersji infix notation na Abstract Syntax Tree (AST).

Składnia DSL:
    - Operatory: AND, OR, NOT (case-insensitive)
    - Nawiasy: ( ) dla grupowania
    - Tagi: facet:key (np. dem:age-25-34, geo:warsaw)

Przykłady:
    - "dem:age-25-34 AND geo:warsaw"
    - "(psy:high-openness OR psy:high-extraversion) AND NOT dem:age-55-plus"
    - "biz:premium-segment AND ctx:holiday-shopping"

AST Node Types:
    - TagNode: pojedynczy tag (leaf node)
    - AndNode: operator AND (binary node)
    - OrNode: operator OR (binary node)
    - NotNode: operator NOT (unary node)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Union, Optional

from app.utils.tags import validate_tag, TagValidationError


class TokenType(Enum):
    """Typy tokenów w DSL."""
    TAG = "TAG"              # facet:key
    AND = "AND"              # operator AND
    OR = "OR"                # operator OR
    NOT = "NOT"              # operator NOT
    LPAREN = "LPAREN"        # (
    RPAREN = "RPAREN"        # )
    EOF = "EOF"              # koniec inputu


@dataclass
class Token:
    """Token w DSL."""
    type: TokenType
    value: str
    position: int


class DSLParseError(ValueError):
    """Błąd parsowania DSL."""
    pass


# === AST Node Types ===

@dataclass
class TagNode:
    """
    Node reprezentujący pojedynczy tag (leaf node).

    Attributes:
        tag: Tag w formacie "facet:key" (znormalizowany)
    """
    tag: str

    def __repr__(self) -> str:
        return f"Tag({self.tag!r})"


@dataclass
class AndNode:
    """
    Node reprezentujący operator AND (binary node).

    Attributes:
        left: Lewe poddrzewo
        right: Prawe poddrzewo
    """
    left: ASTNode
    right: ASTNode

    def __repr__(self) -> str:
        return f"AND({self.left}, {self.right})"


@dataclass
class OrNode:
    """
    Node reprezentujący operator OR (binary node).

    Attributes:
        left: Lewe poddrzewo
        right: Prawe poddrzewo
    """
    left: ASTNode
    right: ASTNode

    def __repr__(self) -> str:
        return f"OR({self.left}, {self.right})"


@dataclass
class NotNode:
    """
    Node reprezentujący operator NOT (unary node).

    Attributes:
        operand: Negowane poddrzewo
    """
    operand: ASTNode

    def __repr__(self) -> str:
        return f"NOT({self.operand})"


# Type alias dla wszystkich node types
ASTNode = Union[TagNode, AndNode, OrNode, NotNode]


# === Lexer (Tokenizacja) ===

class Lexer:
    """
    Lexer - tokenizuje DSL input na stream tokenów.

    Rozpoznaje:
    - Tagi (facet:key)
    - Operatory (AND, OR, NOT)
    - Nawiasy (( ))
    """

    # Regex dla tokenów
    TAG_PATTERN = re.compile(r'[a-z0-9_-]+:[a-z0-9_-]+', re.IGNORECASE)
    OPERATOR_PATTERN = re.compile(r'\b(AND|OR|NOT)\b', re.IGNORECASE)
    PAREN_PATTERN = re.compile(r'[()]')
    WHITESPACE_PATTERN = re.compile(r'\s+')

    def __init__(self, input_text: str):
        """
        Inicjalizuje lexer.

        Args:
            input_text: DSL query string
        """
        self.input = input_text.strip()
        self.position = 0
        self.tokens: List[Token] = []

    def tokenize(self) -> List[Token]:
        """
        Tokenizuje input na listę tokenów.

        Returns:
            Lista tokenów

        Raises:
            DSLParseError: Jeśli napotkano niepoprawny znak
        """
        while self.position < len(self.input):
            # Skip whitespace
            if self._match_whitespace():
                continue

            # Try operator (AND, OR, NOT)
            if self._match_operator():
                continue

            # Try parentheses
            if self._match_paren():
                continue

            # Try tag (facet:key)
            if self._match_tag():
                continue

            # Niepoprawny znak
            char = self.input[self.position]
            raise DSLParseError(
                f"Unexpected character '{char}' at position {self.position}"
            )

        # Dodaj EOF token
        self.tokens.append(Token(TokenType.EOF, "", self.position))
        return self.tokens

    def _match_whitespace(self) -> bool:
        """Dopasowuje whitespace i pomija."""
        match = self.WHITESPACE_PATTERN.match(self.input, self.position)
        if match:
            self.position = match.end()
            return True
        return False

    def _match_operator(self) -> bool:
        """Dopasowuje operator (AND, OR, NOT)."""
        match = self.OPERATOR_PATTERN.match(self.input, self.position)
        if match:
            operator = match.group(0).upper()
            token_type = TokenType[operator]  # AND, OR, NOT
            self.tokens.append(Token(token_type, operator, self.position))
            self.position = match.end()
            return True
        return False

    def _match_paren(self) -> bool:
        """Dopasowuje nawias (( lub ))."""
        match = self.PAREN_PATTERN.match(self.input, self.position)
        if match:
            paren = match.group(0)
            token_type = TokenType.LPAREN if paren == '(' else TokenType.RPAREN
            self.tokens.append(Token(token_type, paren, self.position))
            self.position = match.end()
            return True
        return False

    def _match_tag(self) -> bool:
        """Dopasowuje tag (facet:key) i waliduje."""
        match = self.TAG_PATTERN.match(self.input, self.position)
        if match:
            tag = match.group(0)

            # Waliduj i normalizuj tag
            try:
                normalized_tag = validate_tag(tag)
            except TagValidationError as e:
                raise DSLParseError(
                    f"Invalid tag '{tag}' at position {self.position}: {e}"
                )

            self.tokens.append(Token(TokenType.TAG, normalized_tag, self.position))
            self.position = match.end()
            return True
        return False


# === Parser (Shunting Yard Algorithm) ===

class Parser:
    """
    Parser - konwertuje tokeny na AST używając Shunting Yard Algorithm.

    Precedencja operatorów (rosnąco):
    1. OR (najniższa)
    2. AND
    3. NOT (najwyższa)
    """

    # Precedencja operatorów (wyższa wartość = wyższy priorytet)
    PRECEDENCE = {
        TokenType.OR: 1,
        TokenType.AND: 2,
        TokenType.NOT: 3,
    }

    def __init__(self, tokens: List[Token]):
        """
        Inicjalizuje parser.

        Args:
            tokens: Lista tokenów z lexera
        """
        self.tokens = tokens
        self.position = 0
        self.current_token = tokens[0] if tokens else Token(TokenType.EOF, "", 0)

    def parse(self) -> ASTNode:
        """
        Parsuje tokeny na AST.

        Returns:
            Root node AST

        Raises:
            DSLParseError: Jeśli składnia jest niepoprawna
        """
        ast = self._parse_expression()

        # Sprawdź czy wszystkie tokeny zostały skonsumowane
        if self.current_token.type != TokenType.EOF:
            raise DSLParseError(
                f"Unexpected token '{self.current_token.value}' at position {self.current_token.position}"
            )

        return ast

    def _advance(self) -> None:
        """Przechodzi do następnego tokenu."""
        self.position += 1
        if self.position < len(self.tokens):
            self.current_token = self.tokens[self.position]
        else:
            self.current_token = Token(TokenType.EOF, "", self.position)

    def _parse_expression(self, min_precedence: int = 0) -> ASTNode:
        """
        Parsuje wyrażenie z operator precedence (Pratt parser variant).

        Args:
            min_precedence: Minimalna precedencja operatora do przetworzenia

        Returns:
            AST node
        """
        # Parse prefix (NOT lub primary)
        left = self._parse_prefix()

        # Parse infix operators (AND, OR)
        while True:
            op_type = self.current_token.type

            # Sprawdź czy to operator binarny
            if op_type not in (TokenType.AND, TokenType.OR):
                break

            # Sprawdź precedencję
            precedence = self.PRECEDENCE.get(op_type, 0)
            if precedence < min_precedence:
                break

            # Konsumuj operator
            self._advance()

            # Parse prawe poddrzewo (z wyższą precedencją dla lewostronnej asocjatywności)
            right = self._parse_expression(precedence + 1)

            # Zbuduj node
            if op_type == TokenType.AND:
                left = AndNode(left, right)
            elif op_type == TokenType.OR:
                left = OrNode(left, right)

        return left

    def _parse_prefix(self) -> ASTNode:
        """
        Parsuje prefix expression (NOT lub primary).

        Returns:
            AST node
        """
        # NOT operator
        if self.current_token.type == TokenType.NOT:
            self._advance()
            operand = self._parse_prefix()  # Recursively parse NOT operand
            return NotNode(operand)

        # Primary (tag lub nawias)
        return self._parse_primary()

    def _parse_primary(self) -> ASTNode:
        """
        Parsuje primary expression (tag lub nawiasowane wyrażenie).

        Returns:
            AST node
        """
        token = self.current_token

        # Tag
        if token.type == TokenType.TAG:
            self._advance()
            return TagNode(token.value)

        # Nawiasowane wyrażenie
        if token.type == TokenType.LPAREN:
            self._advance()  # Skip '('
            expr = self._parse_expression()

            # Expect ')'
            if self.current_token.type != TokenType.RPAREN:
                raise DSLParseError(
                    f"Expected ')' at position {self.current_token.position}, "
                    f"got '{self.current_token.value}'"
                )
            self._advance()  # Skip ')'

            return expr

        # Niepoprawny token
        raise DSLParseError(
            f"Unexpected token '{token.value}' at position {token.position}"
        )


# === Public API ===

def parse_dsl(query: str) -> ASTNode:
    """
    Parsuje DSL query do AST.

    Args:
        query: DSL query string

    Returns:
        Root node AST

    Raises:
        DSLParseError: Jeśli składnia jest niepoprawna

    Examples:
        >>> ast = parse_dsl("dem:age-25-34 AND geo:warsaw")
        >>> ast
        AND(Tag('dem:age-25-34'), Tag('geo:warsaw'))

        >>> ast = parse_dsl("(psy:high-openness OR psy:high-extraversion) AND NOT dem:age-55-plus")
        >>> # Returns: AND(OR(Tag(...), Tag(...)), NOT(Tag(...)))
    """
    if not query or not query.strip():
        raise DSLParseError("Empty query")

    # Tokenizacja
    lexer = Lexer(query)
    tokens = lexer.tokenize()

    # Parsowanie
    parser = Parser(tokens)
    ast = parser.parse()

    return ast


def ast_to_string(node: ASTNode) -> str:
    """
    Konwertuje AST z powrotem na string DSL (dla debugowania).

    Args:
        node: Root node AST

    Returns:
        DSL query string

    Examples:
        >>> ast = AndNode(TagNode("dem:age-25-34"), TagNode("geo:warsaw"))
        >>> ast_to_string(ast)
        '(dem:age-25-34 AND geo:warsaw)'
    """
    if isinstance(node, TagNode):
        return node.tag

    if isinstance(node, AndNode):
        return f"({ast_to_string(node.left)} AND {ast_to_string(node.right)})"

    if isinstance(node, OrNode):
        return f"({ast_to_string(node.left)} OR {ast_to_string(node.right)})"

    if isinstance(node, NotNode):
        return f"NOT {ast_to_string(node.operand)}"

    raise ValueError(f"Unknown node type: {type(node)}")
