import unittest
import sqlite3

from models import Model


class TestModel(Model):
    class Meta:
        # See setUp for explanation.
        connection = None


class GoatTest(unittest.TestCase):
    def setUp(self):
        # We need the database to reset after each test, so we recreate it here.
        TestModel.Meta.connection = sqlite3.connect(":memory:")

        TestModel.initialize()
        self.instances = [
            TestModel(foo=1, bar="hi"),
            TestModel(foo="hello", bar="hi"),
            TestModel(foo="hello", bar=None),
        ]

    def test_saving(self):
        for instance in self.instances:
            instance.save()

    def test_find(self):
        for instance in self.instances:
            instance.save()

        instances = list(TestModel.find())

        self.assertEqual(len(instances), 3)
        self.assertEqual(instances, self.instances)

    def test_update(self):
        self.assertEqual(len(list(TestModel.find())), 0)

        for instance in self.instances:
            instance.save()

        for instance in TestModel.find():
            instance.test = 3
            instance.save()

        self.assertEqual(len(list(TestModel.find())), 3)

        for instance in TestModel.find():
            self.assertEqual(instance.test, 3)

    def test_in_place_update(self):
        """
        Test to see if the database behaves properly when inserting items in
        the table we are iterating over.
        """
        for instance in self.instances:
            instance.save()

        for counter, instance in enumerate(TestModel.find()):
            TestModel().save(False)
            self.assertLess(counter, 100)

        self.assertEqual(len(list(TestModel.find())), 6)

    def test_delete(self):
        for instance in self.instances:
            instance.save()

        for instance in TestModel.find():
            instance.delete()

        instances = list(TestModel.find())
        self.assertEqual(instances, [])


if __name__ == '__main__':
    unittest.main()
