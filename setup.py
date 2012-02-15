#!/usr/bin/env python

import sys
assert sys.version >= '2.5', "Requires Python v2.5 or above."
from setuptools import setup

setup(
    name = "goatfish",
    version = "0.1",
    author = "Stochastic Technologies",
    author_email = "info@stochastictechnologies.com",
    url = "https://github.com/stochastic-technologies/goatfish/",
	description = "A small, schemaless ORM that is backed by SQLite.",
	long_description = "Goatfish is a small, schemaless ORM that is backed by SQLite. "
                       "It supports persisting arbitrary objects (anything the pickle "
                       "module can handle) to database and indexing on arbitrary properties "
                       "of the objects.",
	license = "BSD",
    packages = ["goatfish"],
)
