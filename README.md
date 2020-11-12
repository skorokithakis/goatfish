Description
===========

[![Build Status](https://secure.travis-ci.org/stochastic-technologies/goatfish.png?branch=master)](http://travis-ci.org/stochastic-technologies/goatfish)
[![Code Shelter](https://www.codeshelter.co/static/badges/badge-flat.svg)](https://www.codeshelter.co/)


``goatfish`` is a small, schemaless ORM that is backed by SQLite.

It's also this:

![A goatfish](https://upload.wikimedia.org/wikipedia/commons/d/da/Parupeneus_insularis.jpg)

Its usage is very simple, just have your classes inherit from ``goatfish.Model``
and and specify a connection, and the goatfish methods are available to you.
goatfish also supports querying for arbitrary properties in your models, as
well as indexing on arbitrary properties. It does not enforce a schema of any
kind.

It appears that this method is identical to what FriendFeed used to implement
a schemaless layer over MySQL, which is pretty significant validation:

http://backchannel.org/blog/friendfeed-schemaless-mysql


Usage
-----

To use ``goatfish``, all you need to do is create a class that inherits from
``goatfish.Model``:

    import goatfish
    import sqlite3

    db_connection = sqlite3.connect(":memory:")

    class Test(goatfish.Model):
        class Meta:
            # This is so we know where to connect.
            connection = db_connection
            indexes = (
                ("foo",),
                ("foo", "bar"),
            )

    # Create the necessary tables. If they exist, do nothing.
    Test.initialize()

    foo = Test()
    foo.foo = "hi"
    foo.bar = "hello"
    foo.save()

    # Retrieve all elements.
    >>> [test.bar for test in Test.all()]
    ['hello']

    # Count the number of elements.
    >>> Test.count(foo="hi")
    1

    # Run a query with parameters (slow, loads every item from the DB to check it).
    >>> [test.bar for test in Test.find(bar="hello")]
    ['hello']

    # This uses an index, so it's fast.
    >>> [test.foo for test in Test.find(foo="hi"})]
    ['hi']

    # Run a query with a parameter that doesn't exist in the dataset.
    >>> [test.bar for test in Test.find({bar="hello", baz="hi"})]
    []

    >>> Test.find_one(bar="hello").foo
    "hi"

    >>> print(Test.find_one(bar="doesn't exist"))
    None

    # Delete the element.
    >>> foo.delete()

    # Try to retrieve all elements again.
    >>> [test.bar for test in Test.find()]
    []


Indexes
-------

What sets ``goatfish`` apart from other modules such as ``shelve``, ``zodb``,
etc is its ability to query random attributes, and make those queries faster
by using SQLite indexes.

The way this is achieved is by creating an intermediate table for each index
we specify. The index tables consist of the uuid column, and one column for
every field in the index. This way, we can store the value itself in these
index tables and query them quickly, as the rows have SQLite indexes
themselves.

The find() method uses these indexes automatically, if they exist, to avoid
sequential scans. It will automatically use the largest index that contains
the data we want to query on, so a query of ``{"foo": 3, "bar": 2}`` when only
``foo`` is indexed will use the index on ``foo`` to return the data, and do a
sequential scan to match ``bar``.

Right now, new indexes are only populated with data on save(), so you might
miss rows when querying on indexes that are not ready yet. To populate indexes,
go through the objects in your model and perform a save() in each of them.
Convenience functions to populate single indexes will be provided shortly.


Installation
------------

To install ``goatfish`` you need:

* Python 3.4 or later.

You have multiple options for installation:

* With pip (preferred), do ``pip install goatfish``.
* With setuptools, do ``easy_install goatfish``.
* To install from source, download it from
  https://github.com/stochastic-technologies/goatfish/ and do
  ``python setup.py install``.


License
-------

``goatfish`` is distributed under the BSD license.
