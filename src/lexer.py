from tokens import Token, TokenType, KEYWORDS


class LexicalError(Exception):
    def __init__(self, message, line, column):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"Line {line}, Column {column}: {message}")


class Lexer:
    def __init__(self, source):
        self.source = source
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens = []

    def tokenize(self):
        while self.position < len(self.source):
            current = self.source[self.position]

            if current in " \t\r":
                self._advance()
                continue

            if current == "\n":
                self._advance_newline()
                continue

            if current.isalpha() or current == "_":
                self._read_word()
                continue

            if current.isdigit():
                self._read_number()
                continue

            if current == "'":
                self._read_string()
                continue

            if current == ",":
                self._add_token(TokenType.COMMA, ",")
                self._advance()
                continue

            if current == ";":
                self._add_token(TokenType.SEMICOLON, ";")
                self._advance()
                continue

            if current in "=><":
                self._read_operator()
                continue

            raise LexicalError(
                f"Unexpected character {current!r}", self.line, self.column
            )

        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return self.tokens

    def _read_word(self):
        start_line, start_column = self.line, self.column
        start = self.position
        while self.position < len(self.source) and (
            self.source[self.position].isalnum() or self.source[self.position] == "_"
        ):
            self._advance()
        value = self.source[start:self.position]
        token_type = TokenType.KEYWORD if value.upper() in KEYWORDS else TokenType.IDENTIFIER
        self.tokens.append(Token(token_type, value.upper() if token_type == TokenType.KEYWORD else value, start_line, start_column))

    def _read_number(self):
        start_line, start_column = self.line, self.column
        start = self.position
        while self.position < len(self.source) and self.source[self.position].isdigit():
            self._advance()
        if self.position < len(self.source) and self.source[self.position] == ".":
            self._advance()
            while self.position < len(self.source) and self.source[self.position].isdigit():
                self._advance()
        value = self.source[start:self.position]
        self.tokens.append(Token(TokenType.NUMBER, value, start_line, start_column))

    def _read_string(self):
        start_line, start_column = self.line, self.column
        self._advance()
        start = self.position
        while self.position < len(self.source) and self.source[self.position] != "'":
            if self.source[self.position] == "\n":
                self._advance_newline()
            else:
                self._advance()
        if self.position >= len(self.source):
            raise LexicalError("Unterminated string literal", start_line, start_column)
        value = self.source[start:self.position]
        self._advance()
        self.tokens.append(Token(TokenType.STRING, value, start_line, start_column))

    def _read_operator(self):
        start_line, start_column = self.line, self.column
        current = self.source[self.position]
        self._advance()
        if current in "><" and self.position < len(self.source) and self.source[self.position] == "=":
            current += "="
            self._advance()
        self.tokens.append(Token(TokenType.OPERATOR, current, start_line, start_column))

    def _add_token(self, token_type, value):
        self.tokens.append(Token(token_type, value, self.line, self.column))

    def _advance(self):
        self.position += 1
        self.column += 1

    def _advance_newline(self):
        self.position += 1
        self.line += 1
        self.column = 1
