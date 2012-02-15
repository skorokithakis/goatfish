import pickle
import sqlite3
import uuid


class Model(object):
    _serializer = pickle

    @classmethod
    def _get_cursor(cls):
        if cls.Meta.connection is None: raise RuntimeError("Cannot proceed without a database connection")
        return cls.Meta.connection.cursor()

    @classmethod
    def _unmarshal(cls, attributes):
        """
        Create an object from the values retrieved from the database.
        """
        instance = cls.__new__(cls)
        instance.__dict__ = attributes
        return instance

    @classmethod
    def find(cls, parameters=None):
        cursor = cls._get_cursor()
        cursor.execute("""SELECT * FROM %s;""" % cls.__name__.lower())

        # Look through every row.
        for id, uuid, data in cursor:
            loaded_dict = cls._serializer.loads(data.encode("utf-8"))
            loaded_dict["id"] = uuid

            if parameters is None:
                # If there's no query, get everything.
                yield cls._unmarshal(loaded_dict)
            else:
                # Otherwise, make sure every field matches.
                if all((loaded_dict.get(field, None) == parameters[field]) for field in parameters):
                    yield cls._unmarshal(loaded_dict)

    @classmethod
    def initialize(cls):
        """
        Create the necessary tables in the database.
        """
        cursor = cls._get_cursor()
        statement = """CREATE TABLE IF NOT EXISTS %s ( "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "uuid" TEXT NOT NULL, "data" BLOB NOT NULL);""" % cls.__name__.lower()
        cursor.execute(statement)
        statement = """CREATE UNIQUE INDEX IF NOT EXISTS "%s_uuid_index" on %s (uuid ASC)""" % (cls.__name__.lower(), cls.__name__.lower())
        cursor.execute(statement)

    @classmethod
    def commit(cls):
        """
        Commit to the database.
        """
        cls.Meta.connection.commit()

    def __init__(self, *args, **kwargs):
        # Initialize with properties.
        self.__dict__ = kwargs

    def __eq__(self, other):
        if getattr(self, "id", None) is None:
            return False
        elif getattr(other, "id", None) is None:
            return False
        else:
            return self.id == other.id

    def save(self, commit=True):
        """
        Persist an object to the database.
        """
        cursor = self._get_cursor()

        if self.__dict__.get("id", None) is None:
            object_id = uuid.uuid4().hex
            statement = """INSERT INTO %s ("uuid", "data") VALUES (?, ?)""" % self.__class__.__name__.lower()
            cursor.execute(statement, (object_id, self._serializer.dumps(self.__dict__)))
        else:
            # Temporarily delete the id so it doesn't get stored.
            object_id = self.id
            del self.id

            statement = """UPDATE %s SET "data" = ? WHERE "uuid" = ?""" % self.__class__.__name__.lower()
            cursor.execute(statement, (self._serializer.dumps(self.__dict__), object_id))

        # Restore the id.
        self.id = object_id

        if commit:
            self.commit()


    def delete(self, commit=True):
        """
        Delete an object from the database.
        """
        cursor = self._get_cursor()
        statement = """DELETE FROM %s WHERE "uuid" == ?""" % self.__class__.__name__.lower()
        cursor.execute(statement, (self.id, ))

        if commit:
            self.commit()

    class Meta:
        connection = None


