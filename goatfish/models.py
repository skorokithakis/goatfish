import pickle
import sqlite3
import uuid


class Model(object):
    _serializer = pickle

    @classmethod
    def _get_index_table_names(cls, indexes):
        """
        Get the names for the index tables in this model.

        Arguments:
        cls - The class or instance value.
        indexes - The names of the indexes to return table names for.

        Returns:
        (index_name, (index,)) - A tuple of table and field names.
        """
        try:
            class_name = cls.__name__
        except AttributeError:
            # This is not a class, it's an instance. Get the class name.
            class_name = cls.__class__.__name__

        class_name = class_name.lower()

        return [("%s_%s" % (class_name, "_".join(index)), index) for index in indexes]

    @classmethod
    def _get_largest_index(cls, fields):
        """
        Return the largest index that can serve a query on these fields.
        """
        # Turn the attributes and indexes into sets.
        field_set = set(fields)
        indexes = [(set(index), index) for index in cls.Meta.indexes]

        # Compare each index set to the field set only if it contains all parameters.
        # XXX: If the database can use partial indexes, we might not need to only
        # select subsets of the parameters here.
        coverage = [(len(field_set - index[0]), index[1]) for index in indexes if field_set >= index[0]]

        if not coverage:
            return []

        # Return the index that has the most fields in common with the query.
        return min(coverage)[1]

    @classmethod
    def _get_cursor(cls):
        if cls.Meta.connection is None: raise RuntimeError("Cannot proceed without a database connection.")
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
    def find_one(cls, parameters=None):
        """
        Return just one item.
        """
        generator = cls.find(parameters)
        try:
            item = next(generator)
        except NameError:
            item = generator.next()
        except StopIteration:
            item = None
        return item

    @classmethod
    def find(cls, parameters=None):
        """
        Query the database.
        """
        cursor = cls._get_cursor()

        # If we can use an index, we will offload some of the fields to query
        # to the database, and handle the rest here.
        if parameters is None:
            parameters = {}
            index = []
        elif "id" in parameters:
            index = ["id"]
        else:
            index = cls._get_largest_index(parameters.keys())

        table_name = cls.__name__.lower()
        if not index:
            # Look through every row.
            statement = """SELECT * FROM %s;""" % table_name
            cursor.execute(statement)
        elif index == ["id"]:
            # If the object id is in the parameters, use only that, since it's
            # the fastest thing we can do.
            statement = """SELECT * FROM %s WHERE uuid=?;""" % table_name
            cursor.execute(statement, (parameters["id"],))
            del parameters["id"]
        else:
            statement = """SELECT x.id, x.uuid, x.data FROM
                %(table_name)s x INNER JOIN %(index_name)s y
                ON x.uuid = y.uuid
                WHERE %(query)s;""" % {
                    "table_name": table_name,
                    "index_name": table_name + "_" + "_".join(index),
                    "query": " = ? AND ".join(index) + " = ?",
                }
            cursor.execute(statement, [parameters[value] for value in index])

            # Delete the (now) unnecessary parameters, because the database
            # made sure they match.
            for field in index:
                del parameters[field]

        for id, uuid, data in cursor:
            encoded_data = data if type(data) is bytes else data.encode("utf-8")
            loaded_dict = cls._serializer.loads(encoded_data)
            loaded_dict["id"] = uuid

            if parameters:
                # If there are fields left to match, match them.
                if all((loaded_dict.get(field, None) == parameters[field]) for field in parameters):
                    yield cls._unmarshal(loaded_dict)
            else:
                # Otherwise, just return the object.
                yield cls._unmarshal(loaded_dict)

    @classmethod
    def initialize(cls):
        """
        Create the necessary tables in the database.
        """
        cursor = cls._get_cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS %s ( "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "uuid" TEXT NOT NULL, "data" BLOB NOT NULL);""" % cls.__name__.lower())
        cursor.execute("""CREATE UNIQUE INDEX IF NOT EXISTS "%s_uuid_index" on %s (uuid ASC)""" % (cls.__name__.lower(), cls.__name__.lower()))

        for index in cls.Meta.indexes:
            # Create an index table.
            table_name = "%s_%s" % (cls.__name__.lower(), "_".join(index))
            statement = """CREATE TABLE IF NOT EXISTS %s ( "uuid" TEXT NOT NULL""" % table_name
            for field in index:
                statement += """, "%s" TEXT""" % field
            statement += ")"
            cursor.execute(statement)

            # Create the index table index.
            fields = " ASC, ".join(index)
            statement = """CREATE INDEX IF NOT EXISTS "%s_index" on %s (%s ASC)""" % (table_name, table_name, fields)
            cursor.execute(statement)


    @classmethod
    def commit(cls):
        """
        Commit to the database.
        """
        cls.Meta.connection.commit()

    def __init__(self, *args, **kwargs):
        """
        Initialize with properties.
        """
        self.__dict__ = kwargs

    def __eq__(self, other):
        """
        Test for equality,
        """
        if getattr(self, "id", None) is None:
            return False
        elif getattr(other, "id", None) is None:
            return False
        else:
            return self.id == other.id

    def _populate_index(self, cursor, table_name, field_names):
        # Get the values of the indexed attributes from the current object.
        values = []
        for field_name in field_names:
            # Abort if the attribute doesn't exist, we don't need to add it.
            # We check this way to make sure the attribute doesn't exist and is
            # set to None.
            if field_name not in self.__dict__:
                return
            values.append(getattr(self, field_name))

        values.insert(0, self.id)

        # Construct the SQL statement.
        statement = """INSERT OR REPLACE INTO %s ("uuid", "%s") VALUES (%s);""" % (table_name, '", "'.join(field_names), ("?, " * len(values))[:-2])

        cursor.execute(statement, values)

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

        # Insert into all indexes:
        for table_name, field_names in self._get_index_table_names(self.Meta.indexes):
            self._populate_index(cursor, table_name, field_names)

        if commit:
            self.commit()

    def delete(self, commit=True):
        """
        Delete an object from the database.
        """
        cursor = self._get_cursor()
        # Get the name of the main table.
        table_names = [self.__class__.__name__.lower()]
        # The names of all the index tables.
        table_names.extend([result[0] for result in self._get_index_table_names(self.Meta.indexes)])

        # And delete the rows from all of them.
        for table_name in table_names:
            statement = """DELETE FROM %s WHERE "uuid" == ?""" % table_name
            cursor.execute(statement, (self.id, ))

        if commit:
            self.commit()

    class Meta:
        connection = None
        indexes = ()

