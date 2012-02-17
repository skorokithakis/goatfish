import unittest
import sqlite3

import models


class GoatTest(unittest.TestCase):
    def setUp(self):
        # We need this to reset before each test, so we need it in here.
        class TestModel(models.Model):
            class Meta:
                connection = sqlite3.connect(":memory:")
                indexes = (
                    ("foo",),
                    ("foo", "bar"),
            )

        self.TestModel = TestModel
        self.TestModel.initialize()
        self.instances = [
            self.TestModel(foo=1, bar="hi", baz=True),
            self.TestModel(foo="hello", bar="hi", baz=False),
            self.TestModel(foo="hello", bar=None, baz=2),
        ]

    def test_saving(self):
        for instance in self.instances:
            instance.save()

    def test_index_selection(self):
        self.TestModel.Meta.indexes = (
            [1],
            [1, 2],
            [2, 3],
            [2, 3, 5, 6],
            [3, 4],
            [3],
        )
        result = self.TestModel._get_largest_index([1])
        self.assertEqual(result, [1])

        result = self.TestModel._get_largest_index([1, 3])
        self.assertEqual(result, [1])

        # We shouldn't return indexes for which we have no parameters.
        result = self.TestModel._get_largest_index([2, 3, 5])
        self.assertEqual(result, [2, 3])

        result = self.TestModel._get_largest_index([2, 3])
        self.assertEqual(result, [2, 3])

        result = self.TestModel._get_largest_index([2, 3, 5, 6])
        self.assertEqual(result, [2, 3, 5, 6])

        result = self.TestModel._get_largest_index([4])
        self.assertFalse(result)

        result = self.TestModel._get_largest_index([2, 3, 4, 5, 6, 7])
        self.assertEqual(result, [2, 3, 5, 6])

        result = self.TestModel._get_largest_index([5])
        self.assertFalse(result)

    def test_indexes(self):
        for instance in self.instances:
            instance.save()

        indexes = self.TestModel._get_index_table_names(self.TestModel.Meta.indexes)
        self.assertEqual(indexes,
            [("testmodel_foo", ("foo",)), ("testmodel_foo_bar", ("foo", "bar"))])

        connection = self.TestModel.Meta.connection

        # Check that all the index tables have been created properly.
        for table_name, index in indexes:
            results = connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
            self.assertEqual(len(results.fetchall()), 1)

        # Test that they have data in them.
        for table_name, index in indexes:
            results = connection.execute("SELECT count(1) FROM %s;" % table_name)
            self.assertEqual(results.fetchall()[0][0], len(self.instances))

        # Delete the instances.
        for instance in self.TestModel.find():
            instance.delete()

        # Check that they're gone.
        for table_name, index in indexes:
            results = connection.execute("SELECT count(1) FROM %s;" % table_name)
            self.assertEqual(results.fetchall()[0][0], 0)

    def test_find(self):
        for instance in self.instances:
            instance.save()

        instances = list(self.TestModel.find())

        self.assertEqual(len(instances), 3)
        self.assertEqual(instances, self.instances)

    def test_find_one(self):
        for instance in self.instances:
            instance.save()

        instance = self.TestModel.find_one({"id": self.instances[0].id})
        self.assertEqual(instance, self.instances[0])

        instance = self.TestModel.find_one({"foo": "hello"})
        self.assertEqual(instance, self.instances[1])

        instance = self.TestModel.find_one({"bar": "hi"})
        self.assertEqual(instance, self.instances[0])

        instance = self.TestModel.find_one({"baz": True})
        self.assertEqual(instance, self.instances[0])

        instance = self.TestModel.find_one({"baz": "nope"})
        self.assertTrue(instance is None)

    def test_find_by(self):
        for instance in self.instances:
            instance.save()

        instances = list(self.TestModel.find({"id": self.instances[0].id}))
        self.assertEqual(instances, self.instances[0:1])

        instances = list(self.TestModel.find({"id": self.instances[0].id, "foo": 1}))
        self.assertEqual(instances, self.instances[0:1])

        instances = list(self.TestModel.find({"id": self.instances[0].id, "foo": 2}))
        self.assertEqual(instances, [])

        instances = list(self.TestModel.find({"foo": "hello"}))
        self.assertEqual(instances, self.instances[1:])

        instances = list(self.TestModel.find({"foo": 1}))
        self.assertEqual(instances, self.instances[0:1])

        instances = list(self.TestModel.find({"bar": "hi"}))
        self.assertEqual(instances, self.instances[:2])

        instances = list(self.TestModel.find({"foo": 1, "bar": "hi"}))
        self.assertEqual(instances, self.instances[0:1])

        instances = list(self.TestModel.find({"bar": None}))
        self.assertEqual(instances, self.instances[2:])

        instances = list(self.TestModel.find({"baz": True}))
        self.assertEqual(instances, self.instances[0:1])

        instances = list(self.TestModel.find({"baz": False}))
        self.assertEqual(instances, self.instances[1:2])

    def test_update(self):
        self.assertEqual(len(list(self.TestModel.find())), 0)

        for instance in self.instances:
            instance.save()

        for instance in self.TestModel.find():
            instance.test = 3
            instance.save()

        self.assertEqual(len(list(self.TestModel.find())), 3)

        for instance in self.TestModel.find():
            self.assertEqual(instance.test, 3)

    def test_delete(self):
        for instance in self.instances:
            instance.save()

        for instance in self.TestModel.find():
            instance.delete()

        instances = list(self.TestModel.find())
        self.assertEqual(instances, [])


if __name__ == '__main__':
    unittest.main()
