from mylexer import lexer, tokens
import ply.yacc as yacc
import operator

precedence = (
    ('left', 'ADDOP'),
    ('left', 'MULOP'),
)

ops = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.truediv
}


def p_expression_binop(t):
    '''expression : expression ADDOP expression
                  | expression MULOP expression'''
    left, op, right = t[1:]
    t[0] = ops[op](left, right)


def p_expression_group(t):
    'expression : LPAREN expression RPAREN'
    t[0] = t[2]


def p_expression_number(t):
    'expression : NUMBER'
    t[0] = t[1]


parser = yacc.yacc()


def parse(inp):
    return parser.parse(inp, lexer=lexer)

