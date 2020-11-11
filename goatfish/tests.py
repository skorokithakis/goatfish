import sqlite3
import unittest

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

    def test_find(self):
        for instance in self.instances:
            instance.save()

        instances = list(self.TestModel.find())

        self.assertEqual(len(instances), 3)
        self.assertEqual(instances, self.instances)

    def test_find_one(self):
        for instance in self.instances:
            instance.save()

        instance = self.TestModel.find_one(**{"id": self.instances[0].id})
        self.assertEqual(instance, self.instances[0])

        instance = self.TestModel.find_one(**{"foo": "hello"})
        self.assertEqual(instance, self.instances[1])

        instance = self.TestModel.find_one(**{"bar": "hi"})
        self.assertEqual(instance, self.instances[0])

        instance = self.TestModel.find_one(**{"baz": True})
        self.assertEqual(instance, self.instances[0])

        instance = self.TestModel.find_one(**{"baz": "nope"})
        self.assertTrue(instance is None)

    def test_count(self):
        for instance in self.instances:
            instance.save()

        self.assertEqual(self.TestModel.count(), 3)
        self.assertEqual(self.TestModel.count(foo="hello"), 2)
        self.assertEqual(self.TestModel.count(foo="hi"), 0)
        self.assertEqual(self.TestModel.count(id=1), 1)
        self.assertEqual(self.TestModel.count(bar=None), 1)
        self.assertEqual(self.TestModel.count(baz=None), 0)

    def test_find_by(self):
        for instance in self.instances:
            instance.save()

        instances = list(self.TestModel.find(**{"id": self.instances[0].id}))
        self.assertEqual(instances, self.instances[0:1])

        instances = list(self.TestModel.find(**{"id": self.instances[0].id, "foo": 1}))
        self.assertEqual(instances, self.instances[0:1])

        instances = list(self.TestModel.find(**{"id": self.instances[0].id, "foo": 2}))
        self.assertEqual(instances, [])

        instances = list(self.TestModel.find(**{"foo": "hello"}))
        self.assertEqual(instances, self.instances[1:])

        instances = list(self.TestModel.find(**{"foo": 1}))
        self.assertEqual(instances, self.instances[0:1])

        instances = list(self.TestModel.find(**{"bar": "hi"}))
        self.assertEqual(instances, self.instances[:2])

        instances = list(self.TestModel.find(**{"foo": 1, "bar": "hi"}))
        self.assertEqual(instances, self.instances[0:1])

        instances = list(self.TestModel.find(**{"bar": None}))
        self.assertEqual(instances, self.instances[2:3])

        instances = list(self.TestModel.find(**{"baz": True}))
        self.assertEqual(instances, self.instances[0:1])

        instances = list(self.TestModel.find(**{"baz": False}))
        self.assertEqual(instances, self.instances[1:2])

    def _test_update(self):
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


if __name__ == "__main__":
    unittest.main()
