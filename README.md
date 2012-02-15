Description
===========

``goatfish`` is a small, schemaless ORM that is backed by SQLite.

It's also this:

![A goatfish](http://upload.wikimedia.org/wikipedia/commons/thumb/2/22/Parupeneus_insularis_.jpg/300px-Parupeneus_insularis_.jpg)

Its usage is very simple, just have your classes inherit from ``goatfish.Model``
and and specify a connection, and the goatfish methods are available to you.
goatfish also supports querying for arbitrary properties in your models, as
well as indexing on arbitrary properties. It does not enforce a schema of any
kind.

It appears that this method is identical to what FriendFeed used to implement
a schemaless layer over MySQL, which is pretty significant validation:

http://backchannel.org/blog/friendfeed-schemaless-mysql

Installation
------------

To install ``goatfish`` you need:

* Python 2.5 or later in the 2.x line (3.x and earlier than 2.5 not tested).

You have multiple options of installation:

* With pip (preferred), do ``pip install goatfish``.
* With setuptools, do ``easy_install goatfish``.
* To install the source, download it from
  https://github.com/stochastic-technologies/goatfish/ and do
  ``python setup.py install``.

Usage
-----

To use ``goatfish``, all you need to do is create a class that inherits from
``goatfish.Model``:

    import goatfish
    import sqlite3

    class Test(goatfish.Model):
        class Meta:
            # This is so we know where to connect.
            connection = sqlite3.connect(":memory:")

    # Create the necessary tables. If they exist, do nothing.
    Test.initialize()

    foo = Test()
    foo.bar = "hello"
    foo.save()

    # Retrieve all elements.
    >>> [test.bar for test in Test.find()]
    ['hello']

    # Run a query with parameters (slow, loads every item from the DB to check it).
    >>> [test.bar for test in Test.find({"bar": "hello"})]
    ['hello']

    # Run a query with a parameter that doesn't exist in the dataset.
    >>> [test.bar for test in Test.find({"bar": "hello", "baz": "hi"})]
    []

    # Delete the element.
    >>> foo.delete()

    # Try to retrieve all elements again.
    >>> [test.bar for test in Test.find()]
    []


License
-------

``goatfish`` is distributed under the BSD license.

