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

These are good examples of the advantages of DSLs. In each of these cases,
trying to express the same concepts in Python would be verbose and
repetitive. This leads to being hard to read and a source of potential bugs.



Python Metaprogramming DSLs
---------------------------

The first place we could obtain a parser for our new DSL is from Python itself.
You've may have done this without even realising you were writing a DSL: using
(or abusing?) Python's own syntax but modifying the way that it is interpreted
to do something more unusual.

It's worth considering as a DSL

* Metaclasses
* Nested context managers and function calls
* Django ORM
* Pony ORM

* Operator overloading
* "Record and playback technique"
* Parse with ``ast`` and then re-interpret with different semantics

Pony ORM
--------

.. code-block:: python

    >>> select(p for p in Person if p.age > 20)[:]

    SELECT "p"."id", "p"."name", "p"."age"
    FROM "Person" "p"
    WHERE "p"."age" > 20

    [Person[2], Person[3]]


Existing Parsers that we have access to
---------------------------------------

* JSON
* YAML
* ``configparsser``

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
