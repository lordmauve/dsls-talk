import ast
from pyparsing import (
    QuotedString, Regex, Forward, ZeroOrMore, Optional, Literal
)
STRING_CONSTANT = QuotedString('\'', escChar='\\', unquoteResults=False)
INT_CONSTANT = Regex(r'-?\d+(?!\.)')
FLOAT_CONSTANT = Regex(r'-?\d*\.\d+')

CONSTANT = STRING_CONSTANT | FLOAT_CONSTANT | INT_CONSTANT
COMMA = Literal(',')

VALUE = Forward()
LIST = Literal('(') + Optional(VALUE + ZeroOrMore(COMMA + VALUE) + Optional(COMMA)) + Literal(')')
VALUE <<= CONSTANT | LIST

CONSTANT.setParseAction(lambda toks: ast.literal_eval(toks[0]))
LIST.setParseAction(lambda toks: [toks[1:-1:2]])


def parse(inp):
    return VALUE.parseString(inp)[0]
