'''
Id:          "$Id: whereexp.py,v 1.9 2015/02/10 14:54:09 daniel.pope Exp $"
Copyright:   Copyright (c) 2013 Bank of America Merrill Lynch
             All Rights Reserved
Description: |
    Parse a where expression from a string.
Test: xbiz.rec.prudence.tests.unittests.test_utils_whereexp
'''

__all__ = ('where', 'formatWhere')

import ast
import operator
from pyparsing import (
    Word, CaselessKeyword, QuotedString, Optional, Literal, alphas,
    alphanums, Regex, StringStart, StringEnd, operatorPrecedence, opAssoc,
    ParserElement, MatchFirst, ZeroOrMore, ParseFatalException
)
from qz.data.where import (
    Where, like, startsWith, endsWith, isNull, isNotNull, Column, Const, inlist, notinlist
)

ParserElement.enablePackrat()
STRING_CONSTANT = (
    QuotedString('\'', escChar='\\', unquoteResults=False) |
    QuotedString('"', escChar='\\', unquoteResults=False)
)
INT_CONSTANT = Regex(r'-?\d+(?!\.)')
FLOAT_CONSTANT = Regex(r'-?\d*\.\d+')

CONSTANT = STRING_CONSTANT | FLOAT_CONSTANT | INT_CONSTANT

# All constants should be interpreted in Python format
CONSTANT.setParseAction(lambda toks: ast.literal_eval(toks[0]))

COMMA = Literal(',')

LIST = Literal('[') + CONSTANT + ZeroOrMore(COMMA + CONSTANT) + Optional(COMMA) + Literal(']')

IDENTIFIER = MatchFirst([
    Word(alphas, alphanums),
    QuotedString('[', endQuoteChar=']')
])
IDENTIFIER.setParseAction(lambda toks: Where(toks[0]))

VALUE = CONSTANT | IDENTIFIER

OPERATOR = MatchFirst([
    Regex(r'==?'),
    Literal('!='),
    Literal('<>'),
    Literal('>='),
    Literal('<='),
    Literal('>'),
    Literal('<'),
    CaselessKeyword('like'),
])


def make_like(a, b):
    if not isinstance(b, basestring):
        raise ValueError("LIKE operator requires a string on the rhs.")
    ps = b.count('%')
    if ps == 0:
        return a == b
    if ps == 1:
        if b.startswith('%'):
            return a << endsWith >> b[1:]
        elif b.endswith('%'):
            return a << startsWith >> b[:-1]
    if ps == 2:
        if b.startswith('%') and b.endswith('%'):
            return a << like >> b[1:-1]
    raise ValueError("Unsupported LIKE pattern '%s'." % b)


OPS = {
    '==': operator.eq,
    '=': operator.eq,
    '!=': operator.ne,
    '<>': operator.ne,
    '<': operator.lt,
    '>': operator.gt,
    '<=': operator.le,
    '>=': operator.ge,
    'like': make_like
}

INFIX_TEST = IDENTIFIER + OPERATOR + VALUE

IS = CaselessKeyword('is')
NOT = CaselessKeyword('not')
NULL = CaselessKeyword('null')
IN = CaselessKeyword('in')
NULL_TEST = IDENTIFIER + IS + NULL
NOT_NULL_TEST = IDENTIFIER + IS + NOT + NULL
INLIST_TEST = IDENTIFIER + IN + LIST
NOT_INLIST_TEST = IDENTIFIER + NOT + IN + LIST
TEST = INFIX_TEST | NULL_TEST | NOT_NULL_TEST | INLIST_TEST | NOT_INLIST_TEST


@INFIX_TEST.setParseAction
def parseTest(toks):
    l, op, r = toks
    return OPS[op](l, r)


@NULL_TEST.setParseAction
def parseNullTest(toks):
    return toks[0] << isNull >> None


@NOT_NULL_TEST.setParseAction
def parseNotNullTest(toks):
    return toks[0] << isNotNull >> None


@LIST.setParseAction
def parseList(toks):
    return [toks[1:-1:2]]


@INLIST_TEST.setParseAction
def parseInList(toks):
    return toks[0] << inlist >> toks[2]


@NOT_INLIST_TEST.setParseAction
def parseNotInList(toks):
    return toks[0] << notinlist >> toks[3]


INFIX_OPS = {
    'and': operator.and_,
    'or': operator.or_
}


def infix(toks):
    toks = toks[0]
    v = toks.pop(0)
    while toks:
        op, r = toks[:2]
        toks = toks[2:]

        try:
            f = INFIX_OPS[op.lower()]
        except KeyError:
            raise ValueError("Invalid op %s" % op)
        v = f(v, r)
    return v


def unary(op):
    def f(toks):
        _, v = toks[0]
        return op(v)
    return f


EXPRESSION = operatorPrecedence(TEST, [
    (NOT, 1, opAssoc.RIGHT, unary(operator.invert)),
    (CaselessKeyword('and') | CaselessKeyword('or'), 2, opAssoc.LEFT, infix),
])

WHEREEXP = StringStart() + EXPRESSION + StringEnd()


def fail(expr, name):
    """Set a fail action to fail immediately if no expression could be parsed."""
    @expr.setFailAction
    def failList(s, loc, expr, err):
        if not isinstance(err, ParseFatalException):
            raise ParseFatalException("Expected %s" % name, loc)


fail(EXPRESSION, 'expression')
fail(LIST, 'list')


def where(expr):
    r"""Parse a where expression from a string.

    For example

        >>> where('a = 1.0')
        (Where('a') == 1.0)

    Column names that contain spaces can be specified in square brackets:

        >>> where('[some col] = [some other col]')
        (Where('some col') == Column('some other col'))

    Integer, float and double- and single-quoted string literals are
    supported. Strings are backslash escaped and support the same set of
    escape sequences as Python strings.

    AND and OR operators are supported, as well as brackets. The comparison
    operators =, !=, <>, <, >, <= and >= are available. Unlike in Python these
    are purely binary operators and cannot be chained.

        >>> where("a > 'foo' and b != 'bar'")
        ((Where('a') > 'foo') & (Where('b') != 'bar'))

    Unary NOT is also supported, with a precedence above that of AND/OR but
    below that of a comparison operator, LIKE etc. It can be used before any
    test or bracketed expression (not within a test):

        >>> where("not a > 'foo' and not (b != 'bar' or c = 'baz')")
        ~(Where('a') > 'foo') & ~((Where('b') != 'bar') | (Where('c') == 'baz'))

    There is some support for a LIKE operator, which performs case-insensitive
    matching with '%' as a wildcard matching zero or more characters. Not all
    patterns can be used at this time; the one that work are:

        >>> where("a LIKE 'foo%')
        (Where('a') << startsWith >> 'foo')

        >>> where("a like '%foo')
        (Where('a') << endsWith >> 'foo')

        >>> where("a LIKE '%foo%')
        (Where('a') << like >> 'foo')

    You can limit by whether a column is null or not. Note the Where object
    representation of this may appear strange.

        >>> where("a IS NULL")
        (Where('a') << isNull >> None)

        >>> where("a IS NOT NULL")
        (Where('a') << isNotNull >> None)

    IN and NOT IN operators test membership of a value in a list. The list is
    specified with square brackets, much like in Python.

        >>> where("a IN [1, 2, 3]")
        (Where('a') << inlist >> [1, 2, 3])

    The parser will allow the mixing of types within an expression, just like
    in Python, but be aware that this will not necessarily be compatible with
    the type system of real SQL databases.

    """
    return WHEREEXP.parseString(expr)[0]


# Logical Operators
LOGICAL = 'and', 'or'


def _format(w, bracket=False, breakAfterLogicOp=False):
    if isinstance(w.left, Column):
        n = w.left.left
        if ' ' in n:
            return '[%s]' % n
        else:
            return n

    if isinstance(w, Const):
        return repr(w.left)

    if w.op:
        if w.op in '!= == <> >= <=':
            exp = '%s %s %s' % (
                _format(w.left), w.op, _format(w.right)
            )
        elif w.op == 'isNull':
            exp = '%s IS NULL' % _format(w.left)
        elif w.op == 'isNotNull':
            exp = '%s IS NOT NULL' % _format(w.left)
        elif w.op == 'like':
            exp = "%s LIKE %r" % (
                _format(w.left),
                '%%%s%%' % w.right.left
            )
        elif w.op == 'startsWith':
            exp = "%s LIKE %r" % (
                _format(w.left),
                '%s%%' % w.right.left
            )
        elif w.op == 'endsWith':
            exp = "%s LIKE %r" % (
                _format(w.left),
                '%%%s' % w.right.left
            )
        elif w.op == 'inlist':
            exp = "%s IN %r" % (
                _format(w.left),
                w.right.left
            )
        elif w.op == 'notinlist':
            exp = "%s NOT IN %r" % (
                _format(w.left),
                w.right.left
            )
        elif w.op == 'not':
            return 'NOT %s' % _format(w.left, breakAfterLogicOp=True, bracket=True)
        elif w.op in LOGICAL:
            # Consider whether we have a left hand side of chained logic ops
            # eg a and b and c, a or b or c
            # If so they can be written without bracketing, but we will write
            # them with breaks ie. breakAfterLogicOp
            if w.left.op == w.op:
                toks = (
                    # and/or are left associative, so only the rhs is bracketed
                    _format(w.left, breakAfterLogicOp=True), w.op.upper(), _format(w.right, bracket=True)
                )
                breakAfterLogicOp = True
            else:
                toks = (
                    _format(w.left, bracket=True), w.op.upper(), _format(w.right, bracket=True)
                )

            if breakAfterLogicOp:
                exp = '%s %s\n%s' % toks
            else:
                exp = ' '.join(toks)

            if bracket:
                indent = ' ' * 4
                return '(\n%s\n)' % (
                    '\n'.join(indent + l for l in exp.splitlines())
                )
        else:
            raise ValueError("Unknown operation %s" % w.op)

        return exp

    raise ValueError("Unsupported object %r" % w)


def formatWhere(where):
    """Format a Where object as a where expression."""
    return _format(where)
