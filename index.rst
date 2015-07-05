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

Let's look at a few of the well known DSLs in Python.

SQL:

.. code-block:: sql

    SELECT p.id, p.name, p.age
    FROM person p
    WHERE p.age > 20
    ORDER by p.name ASC

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

    class ReviewScraper(Scraper):
        category = StringFact("h2/span/text()")
        title = StringFact("h2/text()")
        teaser = StringFact("h2/preceding-sibling::h3//text()")
        description = ListFact("p[@class = 'description'//text()")

        def clean_description(self, value):
            return normalize_space('\n'.join(value))

        def clean_category(self, value):
            return re.sub(':$', '', value)

.. code-block:: python

    >>> ReviewScraper(url)
    {'category': 'Food and drink', 'title': 'Barcelona Tapas', ...}

Metaclasses are clean - there are few drawbacks to using them transparently
in your code apart from potential developer confusion as to why a class
behaves as it does.


Context managers
----------------

I've seen DSLs like this::

    with html():
        with body():
            h1('Context Manager DSLs')
            p('The', bold('with statement'), 'can be used to construct a DSL')

I strongly dislike this kind of thing. Feels very hackish, hard to read, and
actually may include strange implementation bugs.


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

* Comparison operators don't work as expected. This typically bites you in
  tests. I've seen a lot of code written as::

    self.assertEquals(query, expected)

  which actually executes as::

    bool(query == expected)

  which due to the overloaded ``==`` operator, may evaluate as ``True`` for
  all inputs.

So this kind of DSL introduces really hard to spot bugs.


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


Other Parsers that we have access to
------------------------------------

* JSON
* YAML
* ``configparser``

Ansible
-------

Ansible uses a YAML syntax combined with Jinja2 templating.

Parsing our own DSLs
--------------------

* Linewise parsing
* Detour into grammars
* Parsing with PLY
* Parsing with PyParsing


Working with DSLs
-----------------

* IDE support
  * Syntax highlighting
  * Linting

* Convert AST as string


Pros and cons of DSLs
---------------------

But there are drawbacks to defining any new language too. Adding a DSL to your
project makes it less accessible to new developers.

Using any of the DSLs available in Python or in well-known off-the-shelf
packages doesn't suffer from these drawbacks to the same extent, because you
can reasonably expect developers to have some experience in these languages,
as well as investing themselves
