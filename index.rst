The unabridged guide to Domain Specific Languages in Python
===========================================================

What is a Domain Specific Language
----------------------------------

A "domain" means a problem space.

A Domain Specific Language (DSL) can loosely be described as any formal
language that is more appropriate to a specific problem domain than a general
purpose language like Python.

Some Domain Specific Languages might be Turing-complete, meaning they could be
used to solve any programming problem. However they would only be a domain
specific language if they include features targetting one specific application
domain - to make it really easy to write programs that solve problems in that
domain.

A well-known Turing complete DSL is PHP, originally intended for the domain of
writing web applications, and thus allows mixing HTML with code and receiving
pre-bound variables straight out of the request. PHP's original DSL approach is
widely understood to have been a terrible idea, even among PHP developers.

Languages like JSON or YAML are also not DSLs because they are not domain
specific. But mostly you would use these languages to express something domain
specific; contracts on what you encode within JSON or YAML effectively make
a DSL.

Stepping back then, we don't need very much for a language to be a DSL. I'd say
we need a way of expressing domain-specific concepts more effectively than
using plain Python. But we want to write our code in Python, so we need to be
able to parse that language into a representation where it can be directly
operated on in Python.

So we're mainly talking about parsers. A parser is a piece of code that
converts a piece of text into an internal, structured representation called
an **abstract syntax tree**.

Why isn't this talk called "The unabridged guide to parsers"? Because that is
putting the cart before the horse: building a domain specific language is the
goal, extending the expressiveness of Python. There are specific advantages and
drawbacks to going in this direction. Parsers are just a part of how we get
there.


Why would we want to write a DSL
--------------------------------

Let's look at a few of the well known DSLs you might have encountered.

SQL:

.. code-block:: sql

    SELECT p.id, p.name, p.age
    FROM person p
    WHERE p.age > 20
    ORDER by p.name ASC

CSS:

.. code-block:: css

    header#front h1 {
        font-size: 2em;
        color: white;
    }

Regular expressions with `re`::

    r'(?<=[A-Z])[a-z]+'

``configparser``:

.. code-block:: ini

    [ui]
    username = Daniel Pope <mauve@mauveweb.co.uk>

    [extensions]
    rebase =
    mq =

    [merge-tools]
    # Swap the order of panels in meld so that it is easier to move changes
    # from other to local, which is the most common operation
    meld.args=--label='local' $local --label='other' $other --label='base' $base


``str.format()`` and ``datetime.strftime()``/``.__format__()``:

.. code-block:: python

    >>> now = datetime.datetime.now()
    >>> "The time is now {date:%I:%M%p} on {date:%d %B %Y}".format(date=now)
    'The time is now 11:32PM on 05 July 2015'

reStructuredText:

.. code-block:: rst

    Why would we want to write a DSL
    --------------------------------

    Let's look at a few of the well known DSLs in Python.

    .. code-block:: sql

        SELECT p.id, p.name, p.age
        FROM person p
        WHERE p.age > 20
        ORDER by p.name ASC


These are good examples of the advantages of DSLs. In each of these cases,
trying to express the same concepts in Python would be verbose and
repetitive. This leads to being hard to read and a source of potential bugs.

Also notice that some of these DSLs are very much intended for use embedded
within a Python source file. Others are not. But don't underestimate the value
of this. Indeed, Python's triple-quoted strings will let you include longer
sections of DSL code within your programs, therefore behaving like an almost
native extension of Python syntax.


Python Metaprogramming DSLs
---------------------------

The first place we could obtain a parser for our new DSL is from Python itself.
You've may have done this without even realising you were writing a DSL: using
(or abusing?) Python's own syntax but modifying the way that it is interpreted
to do something more unusual.

Once you start to think of this kind of practice as writing a DSL, you can
start to consider the options of this kind of DSL writing over other
approaches.

Let's look at some examples of DSLs implemented in Python syntax.


Metaclasses
-----------

The power of metaclasses is often used to change the nature of a class
definition's semantics.

If you're not familiar with metaclasses, the usual description is that a
metaclass is the type of a type. I don't think that's a massively useful
description. I like to think of a metaclass as a way of customising the thing
that is inserted into your namespace when your class definition ends.::

    >>> class Duck:
    ...    def quack(self):
    ...        print("quack")
    ...
    >>> print(Duck)
    <class '__main__.Duck'>

You probably have a good idea of what that ``Duck`` object does: you could
instantiate it; call a method. These are the **semantics** of a Python class.

But it doesn't have to behave like that at all - it could behave *absolutely
any way you like*. This is a DSL I once wrote for scraping web pages with
``lxml``::

    class ScrapedReview(Scraper):
        category = StringFact("h2/span/text()")
        title = StringFact("h2/text()")
        teaser = StringFact("h2/preceding-sibling::h3//text()")
        description = ListFact("p[@class = 'description'//text()")

        def clean_description(self, value):
            return normalize_space('\n'.join(value))

        def clean_category(self, value):
            return re.sub(':$', '', value)

.. code-block:: python

    >>> r = ScrapedReview(url)
    >>> r.category
    'Food and drink'
    >>> r.title
    'Barcelona Tapas'

Metaclasses are clean - there are few drawbacks to using them transparently
in your code apart from potential developer confusion as to why a class
behaves as it does.


Writing a metaclass
-------------------

.. code-block:: python

    class Fact:
        def __init__(self, xpath):
            self.xpath = xpath

        def query(self, doc):
            return doc.xpath(self.xpath, current=doc)

    class ScraperMeta(type):
        def __new__(cls, name, bases, dict):
            facts = {}
            newdict = {}
            for k, v in dict.itemms():
                which = facts if isinstance(v, Fact) else newdict
                which[k] = v
            newdict['_facts'] = facts
            return type.__new__(cls, name, bases, newdict)

    class Scraper:
        __metaclass__ = ScraperMeta

        def __init__(self, url):
            doc = lxml.etree.parse(url)
            for name, fact in self._facts.items():
                value = fact.get(doc)
                cleaner = getattr(self, 'clean_' + name, None)
                if callable(cleaner):
                    value = cleaner(value)
                setattr(self, name, value)


Context managers
----------------

I've seen DSLs like this::

    with html():
        with body():
            h1('Context Manager DSLs')
            p('The', bold('with statement'), 'can be used to construct a DSL')

I dislike this kind of thing. Feels very hackish, hard to read, and actually
may include strange implementation bugs (for example, if this was implemented
using global state it wouldn't work in a threaded context).


Operator Overloading
--------------------

Spotted in a real codebase::

    >>> w = (Where('age') >= 18) & (Where('nationality') <<inlist>> ['British', 'Spanish'])
    >>> w.tosql()
    'age >= 18 AND nationality in ('British', 'Spanish')

Eek! Note the use of ``&`` to mean 'and' and ``<<inlist>>`` to form some kind
of custom infix operator!

How does that ``<<inlist>>`` even work? Probably something like this::

    class Where:
        def __lshift__(self, op):
            return UnboundExpression(self, op)

    class UnboundExpression:
        ...

        def __rshift__(self, arg):
            return self.op(self.lhs, self.arg)

This is unintuitive and also has bad side-effects:

* ``and`` and ``or`` can not be overloaded in Python. So the DSL uses ``&`` and
  ``|`` instead. These have the wrong **operator precedence**. So this::

    Where('age') >= 18 & Where('nationality') <<inlist>> ['British', 'Spanish']

  will actually be executed as::

    Where('age') >= (18 & Where('nationality')) <<inlist>> ['British', 'Spanish']

  ...which is almost certainly not what is intended.

* Comparison operators don't work as expected. This typically bites you in
  tests. I've seen a lot of code written as::

    self.assertEquals(query, expected)

  which actually executes as::

    bool(query == expected)

  which due to the overloaded ``==`` operator, may evaluate as ``True`` for
  all inputs.

So this kind of DSL introduces really hard to spot bugs.

In general, I wouldn't recommend overloading operators to add radically
different semantics, and certainly not the ``==`` operator, because that will
get used all the time in places you don't expect, like ``x in list``.


AST-based parsing
-----------------

We could have written that last DSL a lot better by using Python's own parser,
exposed via the ``ast`` module. This would let us parse real Python syntax
but then rather than executing it, we could apply our own semantics::

    Person.select("age > 20 and nationality in ['British', 'Spanish']")

The code to do this would look a bit like this::

    import ast

    class SQLTransformer(ast.NodeVisitor):
        def visit_boolop(self, node):
            if node.op == ast.And:
                op = ' AND '
            elif node.op == ast.Or:
                op = ' OR '
            else:
                raise ValueError("Unknown boolean operation %s" % node.op)
            return op.join(self.visit(e) for e in node.values)

        ...

    def select(expr):
        root = ast.parse(expr, mode='eval')
        sql = SQLTransformer().visit(root)

We'll talk a little more about the ``ast`` module later.

I've also seen a DSL that looks like real Python! Eek! ::

    @graphnode
    def PageTitle(self):
        return self.Name or self.Doc.Name

This is parsed by using ``inspect.getsource()`` to find the source and ``ast``
to parse it, rewrite it, and recompile it. I wouldn't recommend this: it's
extremely confusing for the user when their code doesn't execute as expected
(and any debugger breakpoints don't work right when they try to find out why).


Pony ORM
--------

Pony ORM does some amazing, clever hacks to allow this kind of Python-syntax
DSL to be even more succinctly encoded in Python, without even the need for
quotes:

.. code-block:: python

    >>> select(p for p in Person if p.age > 20)[:]

    SELECT "p"."id", "p"."name", "p"."age"
    FROM "Person" "p"
    WHERE "p"."age" > 20

    [Person[2], Person[3]]


Pony does this by "decompiling" Python bytecode (actually the approaches to do
this are similar to the other parsing approaches we will talk about, but act on
Python's binary byte code format rather than text).


Other Parsers that we have access to
------------------------------------

The next class of parsers we have access to are those available in the standard
library or well-known packages, such as ``json``, ``configparser`` or ``yaml``
(or even XML. Eek!)

Each of these formats comes with its own set of syntax that is not necessarily
aligned to your domain.

The ElasticSearch Query DSL, for example, is rather horrific:

.. code-block:: json

    {
        "query": {
            "bool": {
                "must": [{
                    "match_phrase_prefix": {"title": {"query": query, "analyzer": "prose"}}
                }],
                "should": [
                    {"term": {"_type": {"value": "city", "boost": 1.0}}}
                ],
            }
        },
        "fields": ["coding", "primary_city", "city_name", "title", "category"],
        "highlight": {
            "fields": {
                "title": {}
            }
        }
    }

In fairness, this is a wire protocol that you might reasonably be expected to
use a more user friendly binding for. But all the documentation is given in
this format so unless your ElasticSearch bindings reproduce all of
ElasticSearch's documentation ported to show examples with their API, you have
to engage with it to use ElasticSearch.

Ansible uses a combination of YAML and Jinja2:

.. code-block:: yaml

    - user: name={{ item.name }} state=present generate_ssh_key=yes
      with_items: "{{users}}"

    - authorized_key: "user={{ item.0.name }} key='{{ lookup('file', item.1) }}'"
      with_subelements:
         - users
         - authorized


YAML is a complicated language, aiming to be a superset of JSON while being
somewhat more human readable and editable. But there are ugly pitfalls. Spot
the bug in this YAML document:

.. code-block:: yaml

    Terminator (series):
        - The Terminator
        - Terminator 2: Judgement Day
        - Terminator 3: Rise of the Machines
        - Terminator Salvation
        - Terminator Genisys

Or this one:

.. code-block:: yaml

    canada:
        MB: Manitoba
        NS: Nova Scotia
        ON: Ontario
        QC: Quebec
        SK: Saskatchewan


Parsing our own DSLs
--------------------

Understanding that the existing parsers have limitations, the next place we
could logically go to is writing our own parsers.


How to design a DSL
-------------------

In my opinion the best way to start designing your own DSL is to sit down with
a blank page and start expressing the structure you want to work with in a way
that makes sense to you. Then iterate backwards and forwards on this until you
have several examples of your new DSL.

Avoid cramming in lots of syntactic sugar too early: you want to minimise the
complexity of the language.

Make sure you include some facility for comments; indeed, you should liberally
comment what your examples are intended to do.

Focus on creating a small set of syntax that meets your goals: expressiveness
and readability. An additional concern is *parseability*: will you struggle to
write a parser for this language?

Let's now look at some ways of doing this.

Linewise Parsing
----------------

The simplest place to start writing a DSL is by processing each line of input
in turn, maybe matching it with regular expressions. I wrote very useful DSL
based on this for constructing the tabular datastructures that a lot of our
code works with, making it possible to replace code like this::

    t = Table([
        ('int', 'ReviewID'),
        ('str', 'Ticket')
    ])
    t.extend([
        (1000, 'QRX-1'),
        (2000, None),
    ])

with a much more succinct and literate style::

    table_literal("""
    | (int) ReviewID | Ticket |
    | 1000           | QRX-1  |
    | 2000           | None   |
    """)

This is extremely useful for writing readable tests.

You can go an extremely long way by parsing linewise - simply reading a line at
at time and plugging it into a custom finite state machine.

A finite state machine is a system that responds to each input token in a
different way depending on its current state. Some inputs will trigger a state
transition.

For example, you might write::

    state = READ_HEADER
    for line in source.splitlines():
        line = strip_comments(line)
        if state is READ_HEADER:
            if not line:
                state = READ_BODY
                continue

            match = re.match(r'^([^:]+):\s*(.*)', line)
            if match:
                key, value = match.groups()
                headers[key] = value
            else:
                raise ParseError("Invalid header line %s")
        elif state is READ_BODY:
            ...

Or you could use a class-based pattern that offers a bit more structure::

    class MyParser:
        def process_header(self, line):
            if not line:
                self.state = process_body
                return

         def process_body(self, line):
            ...

        INITIAL_STATE = process_header

        def parse(self, f):
            self.state = self.INITIAL_STATE
            for l in f:
                self.state(l)

A plain, off-the-shelf finite state machine is powerful enough to parse all
regular grammars. But by writing it yourself, you can extend it to maintain
other kinds of state, such as a stack, to take this much further.

It should be noted that linewise parsing doesn't mean that language structures
can't span multiple lines. It just means that you're not going to consider
the substructure of the line (except, say, using regular expressions).

This deserves some more consideration. Before we progress, let's look at some
of the underlying theory of parsers.

The Dragon Book
---------------

The classic reference on parsers is *Compilers, Principles, Techniques and
Tools* by Aho, Lam, Sethi and Ullman, ISBN 0321486811, known colloquially as
"The Dragon Book" due to the dragon on its cover.

It's a very thorough mathematical treatment of the subject of compilers, of
which parsers form the first section.

For most software engineers though, implementing your own parser from scratch
is not necessary, because there are plenty of good libraries to do the hard
parts for you.

Before we look at those, we do need to look a little at the basic theory of
parsers.


Lexical Analysis, Syntax Analysis
---------------------------------

Commonly parsers are split into two phases:

* **Lexical Analysis**, (or **tokenisation**) in which a source stream is split
  into a sequence of **tokens**, the "words" and "symbols" that make up a
  program.

* **Syntax Analysis**, in which a sequence of tokens (from the Lexical Analysis
  phase) is transformed into a structure called an **abstract syntax tree**.

Python's standard library exposes implementations of both of these for the
Python's language itself. Lexical Analysis is provided by the ``tokenize``
module. Syntax Analysis is provided by the ``ast`` module.

Let's compare their output on the following expression::

    (x ** y) + 1


Lexical Analysis
----------------

``tokenize`` produces an iterable of tokens that look like this (somewhat
simplified from the actual output):

.. code-block:: python

    [
        (tokens.OP, '('),
        (tokens.NAME, 'x'),
        (tokens.OP, '**'),
        (tokens.NAME, 'y'),
        (tokens.OP, ')'),
        (tokens.OP, '+'),
        (tokens.NUMBER, '1'),
    ]

You can see that it's just a list of the "words" in the program and their
types.


Syntax Analysis
---------------

``ast`` can calculate a structure from the expression. We can assume it's
making use of the token stream from ``tokenize`` as its input, behind the
scenes.

.. code-block:: python

    BinOp(
        left=BinOp(
            left=Name(id='x', ctx=Load()),
            op=Pow(),
            right=Name(id='y', ctx=Load())
        ),
        op=Add(),
        right=Num(n=1)
    )

If you wished to, you could evaluate this by simply walking the syntax tree and
evaluate this by providing your own implementations of the operators.


Returning to linewise parsers
-----------------------------

So this allows us to come back to our discussion of linewise parsers - we
simply treat each line as a "token". We can match the line against a regular
expression to decide on its "type" and other attributes.

This is the approach I took for the DSL in my winning game in October 2014's
Pyweek, *Legend of Goblit*. This was an "adventure stage play" driven by an
executable script, in a language inspired by both dramatic scripts and
reStructuredText.

.. code-block:: restructuredtext

    .. include:: act1defs

    Act 1
    =====

    [pause]
    [GOBLIT enters]
    GOBLIT: Hello?
    WIZARD TOX: hmm?
    [pause]
    GOBLIT: I say, hello? Grand Wizard Tox?
    [WIZARD TOX turns around]
    WIZARD TOX: *sigh* Yes?
    .. choose-all::
        .. choice:: My name is Goblit.
            GOBLIT: I'm Goblit.
            WIZARD TOX: Goblet? That's a strange name.

        .. choice:: About the assistant role?
            GOBLIT: I was told you need an assistant?
            WIZARD TOX: A vacancy has become available, yes.

You can see that there are a few basic line forms (token types), but that the
syntax analysis can produce a tree structure representing possible game
actions. The game engine allows the player to choose how to traverse this tree
and progress the plot.

Grammars
--------

To progress into writing our own parsers, we need to start by thinking about
how we describe the language we want to work with. We can write down a
specification for the structure of a language, which is called a **grammar**.

Much of the literature describing grammars will do so with a semi-formal
language that consists of a list of **productions**. Each production consists
of an AST node type and a number of token sequences that, if spotted in the
input, mean that we can construct an AST node with those tokens as children.

The grammar for a simple calculator expression language may look like this:

.. code-block::

    expr -> expr '+' term | expr '-' term | term

    term -> term '*' factor | term '/' factor | factor

    factor -> '\d+' | '(' expr ')'


Note that this kind of representation shows us the **associativity** and
**operator precedence** of the language - two aspects of how the language
behaves when brackets are omitted. Your language will have to assume some
structure in the absence of brackets, and it's important to get these right
so that users of your language aren't confused about what a program means.

Let's look at the expression::

    a + b + c

If the ``+`` operator is **left associative** then this is equivalent to ::

    (a + b) + c

If it is **right associative** then this is equivalent to ::

    a + (b + c)

Python's operators are *all* left-associative. To avoid confusion for users in
a language that is expected to be used alongside Python, prefer
left-associativity for your DSL operators.

This was the rationale for why the new ``@`` matrix-multiplication operator in
Python 3.5 is left associative (see PEP465_).

.. _PEP465: https://www.python.org/dev/peps/pep-0465/

Operator precedence is about which operators are bracketed *first*. Look at
the expression::

    a + b * c

Standard mathematical rules would bracket this as ::

    a + (b * c)

meaning that ``*`` has higher operator precedence than ``+``. If ``+`` had the
same precedence as ``*`` then the associativity would take over, and the
expression would be parsed as::

    (a + b) * c

Again, the Principal of Least Surprise is required here.


PLY
---

The first of the parser frameworks we will look at is PLY, short for "Python
Lexx Yacc". Lexx is a lexical analyser generator for C; Yacc is a syntax
analyser generator (short for "Yet Another Compiler Compiler"), a parser
generator (using LALR or SLR algorithms).

Correspondingly it works in a very similar way: you define a set of token
regular expressions that can be used to tokenise input. Then you define
grammar productions. Each of these are defined as functions so that you can
customise, when the rule matches, what is inserted into your syntax tree.

Let's write a simple calculator using PLY.

First, we write a lexical analyser:

.. code-block:: python

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


Note how the docstring of the function is used as the regular expression to
match; the function body remaps the value of the token object. If the value
does not need to be mapped, a simple string suffices.

Then we can write the syntax analyser. Here, rather than returning an abstract
syntax tree, we interpret the result immediately.

.. code-block:: python

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

Again, the docstring of each function defines the production to match. The
function body will be called, passing the matches as the list ``t``. The
function can map that set of matched nodes and tokens into something directly
usable.

The ``precedence`` list gives the operator precedence and associativity of the
operators, so this doesn't need to be expressed through the grammar.

Then you could use your new parser like this::

    from myparser import parser
    from mylexer import lexer

    def parse(inp):
        return parser.parse(inp, lexer=lexer)

    inp = input()
    result = parse(inp)
    print(inp, '=', result)


PyParsing
---------

PyParsing implements a very different parsing algorithm called **Recursive
Descent**. It's more powerful than the LR(1) parsers generated by PLY (meaning
it can parse a category of languages that PLY can not) but can be extremely
slow when parsing those grammars.

The significant difference is that PLY will always parse its input in a single
pass and the language must be unambiguous about what are valid next tokens at
each step. PyParsing allows backtracking - searching through approaches to
parsing some input to find the one that works best. This can be very slow so
should not be used unless it's completely necessary.

Like PLY, PyParsing includes a Python DSL for declaring the grammars. This time
it's an operator-overloading style DSL.

.. code-block:: python

    import ast
    from pyparsing import (
        QuotedString, Regex, Forward, ZeroOrMore, Optional, Literal
    )
    STRING_CONSTANT = QuotedString('\'', escChar='\\', unquoteResults=False)
    INT_CONSTANT = Regex(r'-?\d+(?!\.)')
    FLOAT_CONSTANT = Regex(r'-?\d*\.\d+')
    COMMA = Literal(',')

    CONSTANT = STRING_CONSTANT | FLOAT_CONSTANT | INT_CONSTANT

    VALUE = Forward()
    LIST = Literal('(') + Optional(VALUE + ZeroOrMore(COMMA + VALUE) + Optional(COMMA)) + Literal(')')
    VALUE << (CONSTANT | LIST)

    CONSTANT.setParseAction(lambda toks: ast.literal_eval(toks[0]))
    LIST.setParseAction(lambda toks: [toks[1:-1:2]])


Each of the magic PyParsing types can be combined to form new, composite
matcher types. The ``+`` operator means one matcher follows another, the ``|``
operator meaning "the first of these rules that matches". The ``^`` operator
provides the backtracking "the rule that matches most of the string" which will
require every permutation to be considered.

Unlike PLY, which has to compile the whole grammar together, each PyParsing
rule is its own parser:

.. code-block:: python

    inp = input()
    res = VALUE.parseString(inp)[0]
    print(res)


Parsley
-------

There are also other parsers available in Python, such as `Parsley`_.

Parsley takes a single string specifying a grammar in its own grammar DSL.
Tokens, productions and the expressions used to construct the result tree are
all included in the DSL - making it terser but perhaps even harder to use.

.. code-block:: python

    parser = parsley.makeGrammar("""
        number = <digit+>:ds -> int(ds)
        ws = ' '*
        expr = number:left ws ('+' ws number:right -> left + right
                              |'-' ws number:right -> left - right
                              | -> left)
    """)

.. _Parsley: http://parsley.readthedocs.org/en/latest/tutorial.html


Working with DSLs
-----------------

* IDE support
  * Syntax highlighting
  * Linting

* Convert AST to string

* Clear syntax errors
  * should include line number

If indended for use within Python, avoid syntax that could cause problems
with Python's own string escaping. In particular, try to avoid requiring
backslashes in your own DSL, because even with raw strings it is difficult to
mentally parse which backslashes are input to Python and which then become
input to your DSL's parser.


Syntax highlighting
-------------------

An editor's syntax hilighting system wil typically be very similar to the
code for a tokenizer - but that may have to be ported into a language the
editor can understand.

This is an example of writing a syntax highlighter for vim:

.. code-block:: vim-script

    syn keyword Keyword       class define node
    syn keyword Keyword       use metric
    syn keyword Keyword       alert
    syn keyword Label         as format at severity if for value inherits using

    syn match cmpOp '>\|<\|==\|!='
    syn match String '"[^"]*"' contains=Variable,QVariable
    syn match Number '[0-9]\+'
    syn match Number '[0-9]\+[hms]'

    syn match Comment       "\s*#.*$"

    syn match Identifier '[A-Za-z][A-Za-za-z.-]*'

    syn match Variable  "\$\w\+"
    syn match QVariable  "\${\w\+}" contained

    hi link Variable Include
    hi link Label   Type
    hi link cmpOp SpecialChar
    hi link QVariable Variable

    let b:current_syntax = "rule"


Pros and cons of DSLs
---------------------

But there are drawbacks to defining any new language too. Adding a DSL to your
project makes it less accessible to new developers.

Using any of the DSLs available in Python or in well-known off-the-shelf
packages doesn't suffer from these drawbacks to the same extent, because you
can reasonably expect developers to have some experience in these languages,
as well as investing themselves

Costs of writing a new DSL
--------------------------

* IDE support
* Maintenance cost
* Extensibility
  * Depending on your domain, you should have a good idea of the directions in
    which you will need to extend.
* Documentation tools
