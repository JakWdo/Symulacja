"""
Testy dla DSL Parser

Testuje parsowanie zapytań DSL do AST (Abstract Syntax Tree).
"""

import pytest

from app.services.filters.dsl_parser import (
    parse_dsl,
    ast_to_string,
    TagNode,
    AndNode,
    OrNode,
    NotNode,
    DSLParseError,
    Lexer,
    Parser,
)


class TestLexer:
    """Testy dla Lexera (tokenizacja)."""

    def test_tokenize_simple_tag(self):
        """Test tokenizacji pojedynczego tagu."""
        lexer = Lexer("dem:age-25-34")
        tokens = lexer.tokenize()

        assert len(tokens) == 2  # TAG + EOF
        assert tokens[0].value == "dem:age-25-34"
        assert tokens[1].type.value == "EOF"

    def test_tokenize_and_operator(self):
        """Test tokenizacji operatora AND."""
        lexer = Lexer("dem:age-25-34 AND geo:warsaw")
        tokens = lexer.tokenize()

        assert len(tokens) == 4  # TAG + AND + TAG + EOF
        assert tokens[0].value == "dem:age-25-34"
        assert tokens[1].type.value == "AND"
        assert tokens[2].value == "geo:warsaw"

    def test_tokenize_or_operator(self):
        """Test tokenizacji operatora OR."""
        lexer = Lexer("psy:high-openness OR psy:high-extraversion")
        tokens = lexer.tokenize()

        assert tokens[1].type.value == "OR"

    def test_tokenize_not_operator(self):
        """Test tokenizacji operatora NOT."""
        lexer = Lexer("NOT dem:age-55-plus")
        tokens = lexer.tokenize()

        assert tokens[0].type.value == "NOT"
        assert tokens[1].value == "dem:age-55-plus"

    def test_tokenize_parentheses(self):
        """Test tokenizacji nawiasów."""
        lexer = Lexer("(dem:age-25-34 AND geo:warsaw)")
        tokens = lexer.tokenize()

        assert tokens[0].type.value == "LPAREN"
        assert tokens[4].type.value == "RPAREN"

    def test_tokenize_case_insensitive_operators(self):
        """Test case-insensitive operatorów."""
        lexer = Lexer("dem:age-25-34 and geo:warsaw")
        tokens = lexer.tokenize()

        assert tokens[1].value == "AND"  # Normalized to uppercase

    def test_invalid_tag_format(self):
        """Test błędu przy niepoprawnym formacie tagu."""
        lexer = Lexer("invalid-tag")

        with pytest.raises(DSLParseError, match="Invalid tag"):
            lexer.tokenize()


class TestParser:
    """Testy dla Parsera (AST generation)."""

    def test_parse_single_tag(self):
        """Test parsowania pojedynczego tagu."""
        ast = parse_dsl("dem:age-25-34")

        assert isinstance(ast, TagNode)
        assert ast.tag == "dem:age-25-34"

    def test_parse_and_operator(self):
        """Test parsowania operatora AND."""
        ast = parse_dsl("dem:age-25-34 AND geo:warsaw")

        assert isinstance(ast, AndNode)
        assert isinstance(ast.left, TagNode)
        assert isinstance(ast.right, TagNode)
        assert ast.left.tag == "dem:age-25-34"
        assert ast.right.tag == "geo:warsaw"

    def test_parse_or_operator(self):
        """Test parsowania operatora OR."""
        ast = parse_dsl("psy:high-openness OR psy:high-extraversion")

        assert isinstance(ast, OrNode)
        assert ast.left.tag == "psy:high-openness"
        assert ast.right.tag == "psy:high-extraversion"

    def test_parse_not_operator(self):
        """Test parsowania operatora NOT."""
        ast = parse_dsl("NOT dem:age-55-plus")

        assert isinstance(ast, NotNode)
        assert isinstance(ast.operand, TagNode)
        assert ast.operand.tag == "dem:age-55-plus"

    def test_parse_complex_expression(self):
        """Test parsowania złożonego wyrażenia z nawiasami."""
        ast = parse_dsl("(psy:high-openness OR psy:high-extraversion) AND NOT dem:age-55-plus")

        # Root: AND
        assert isinstance(ast, AndNode)

        # Left: OR (w nawiasach)
        assert isinstance(ast.left, OrNode)
        assert ast.left.left.tag == "psy:high-openness"
        assert ast.left.right.tag == "psy:high-extraversion"

        # Right: NOT
        assert isinstance(ast.right, NotNode)
        assert ast.right.operand.tag == "dem:age-55-plus"

    def test_operator_precedence_not_highest(self):
        """Test precedencji - NOT ma najwyższy priorytet."""
        ast = parse_dsl("dem:age-25-34 AND NOT geo:warsaw")

        # AND powinien być root, NOT powinien być prawym poddrzewem
        assert isinstance(ast, AndNode)
        assert isinstance(ast.left, TagNode)
        assert isinstance(ast.right, NotNode)

    def test_operator_precedence_and_over_or(self):
        """Test precedencji - AND ma wyższy priorytet niż OR."""
        ast = parse_dsl("dem:age-25-34 OR geo:warsaw AND psy:high-openness")

        # OR powinien być root (niższa precedencja = wyżej w drzewie)
        # Prawe poddrzewo: AND
        assert isinstance(ast, OrNode)
        assert isinstance(ast.left, TagNode)
        assert ast.left.tag == "dem:age-25-34"

        # Prawe poddrzewo to AND
        assert isinstance(ast.right, AndNode)
        assert ast.right.left.tag == "geo:warsaw"
        assert ast.right.right.tag == "psy:high-openness"

    def test_parentheses_override_precedence(self):
        """Test nawiasów - nadpisują precedencję."""
        ast = parse_dsl("(dem:age-25-34 OR geo:warsaw) AND psy:high-openness")

        # AND powinien być root (z powodu nawiasów)
        assert isinstance(ast, AndNode)

        # Lewe poddrzewo: OR (w nawiasach)
        assert isinstance(ast.left, OrNode)
        assert ast.left.left.tag == "dem:age-25-34"
        assert ast.left.right.tag == "geo:warsaw"

        # Prawe poddrzewo: tag
        assert isinstance(ast.right, TagNode)
        assert ast.right.tag == "psy:high-openness"

    def test_multiple_and_left_associative(self):
        """Test lewostronnej asocjatywności AND."""
        ast = parse_dsl("dem:age-25-34 AND geo:warsaw AND psy:high-openness")

        # ((dem:age-25-34 AND geo:warsaw) AND psy:high-openness)
        assert isinstance(ast, AndNode)
        assert isinstance(ast.left, AndNode)  # Lewostronna asocjatywność
        assert isinstance(ast.right, TagNode)
        assert ast.right.tag == "psy:high-openness"

    def test_empty_query_error(self):
        """Test błędu przy pustym zapytaniu."""
        with pytest.raises(DSLParseError, match="Empty query"):
            parse_dsl("")

        with pytest.raises(DSLParseError, match="Empty query"):
            parse_dsl("   ")

    def test_missing_closing_parenthesis(self):
        """Test błędu przy brakującym nawiasie zamykającym."""
        with pytest.raises(DSLParseError, match="Expected '\\)'"):
            parse_dsl("(dem:age-25-34 AND geo:warsaw")

    def test_unexpected_token(self):
        """Test błędu przy nieoczekiwanym tokenie."""
        with pytest.raises(DSLParseError, match="Unexpected token"):
            parse_dsl("dem:age-25-34 AND")


class TestASTToString:
    """Testy dla konwersji AST do stringu (debugging)."""

    def test_tag_node_to_string(self):
        """Test konwersji TagNode do stringu."""
        ast = TagNode("dem:age-25-34")
        assert ast_to_string(ast) == "dem:age-25-34"

    def test_and_node_to_string(self):
        """Test konwersji AndNode do stringu."""
        ast = AndNode(
            TagNode("dem:age-25-34"),
            TagNode("geo:warsaw")
        )
        assert ast_to_string(ast) == "(dem:age-25-34 AND geo:warsaw)"

    def test_or_node_to_string(self):
        """Test konwersji OrNode do stringu."""
        ast = OrNode(
            TagNode("psy:high-openness"),
            TagNode("psy:high-extraversion")
        )
        assert ast_to_string(ast) == "(psy:high-openness OR psy:high-extraversion)"

    def test_not_node_to_string(self):
        """Test konwersji NotNode do stringu."""
        ast = NotNode(TagNode("dem:age-55-plus"))
        assert ast_to_string(ast) == "NOT dem:age-55-plus"

    def test_complex_expression_to_string(self):
        """Test konwersji złożonego wyrażenia do stringu."""
        ast = AndNode(
            OrNode(
                TagNode("psy:high-openness"),
                TagNode("psy:high-extraversion")
            ),
            NotNode(TagNode("dem:age-55-plus"))
        )
        result = ast_to_string(ast)
        assert "high-openness" in result
        assert "AND" in result
        assert "NOT" in result


# === Integration Tests ===

class TestParseRoundtrip:
    """Testy round-trip: DSL → AST → DSL."""

    @pytest.mark.parametrize("dsl,expected", [
        ("dem:age-25-34", "dem:age-25-34"),
        ("dem:age-25-34 AND geo:warsaw", "(dem:age-25-34 AND geo:warsaw)"),
        ("psy:high-openness OR psy:high-extraversion", "(psy:high-openness OR psy:high-extraversion)"),
        ("NOT dem:age-55-plus", "NOT dem:age-55-plus"),
    ])
    def test_parse_and_back(self, dsl, expected):
        """Test round-trip: parse → to_string."""
        ast = parse_dsl(dsl)
        result = ast_to_string(ast)
        # Może mieć dodatkowe nawiasy, ale powinna zachować semantykę
        assert expected in result or result == expected
