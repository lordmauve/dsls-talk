import ply.lex as lex

tokens = 'ADDOP MULOP LPAREN RPAREN NUMBER'.split()

t_ADDOP = r'[+-]'
t_MULOP = r'[*/]'
t_LPAREN = r'\('
t_RPAREN = r'\)'

def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

t_ignore = ' \t'

lexer = lex.lex()

