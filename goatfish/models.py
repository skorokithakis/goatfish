import json


class Model:
    @classmethod
    def _get_cursor(cls):
        if cls.Meta.connection is None:
            raise RuntimeError("Cannot proceed without a database connection.")
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
    def find_one(cls, **parameters):
        """
        Return just one item.
        """
        generator = cls.find(**parameters)
        try:
            item = next(generator)
        except NameError:
            item = generator.next()
        except StopIteration:
            item = None
        return item

    @classmethod
    def _prepare_statement(cls, parameters, verb="SELECT *"):
        table_name = cls.__name__.lower()

        if parameters:
            param_list = parameters.items()
            if "id" in parameters:
                id = parameters.pop("id")
                statement = "%s FROM %s WHERE %s" % (
                    verb,
                    table_name,
                    " AND ".join(
                        ["id = ?"]
                        + ["json_extract(data, '$.%s') IS ?" % i[0] for i in param_list]
                    ),
                )
                return statement, [id] + [i[1] for i in param_list]
            else:
                statement = "%s FROM %s WHERE %s" % (
                    verb,
                    table_name,
                    " AND ".join(
                        "json_extract(data, '$.%s') IS ?" % i[0] for i in param_list
                    ),
                )
                return statement, [i[1] for i in param_list]
        else:
            statement = "%s FROM %s" % (verb, table_name)
            return statement, ()

    @classmethod
    def count(cls, **parameters):
        """
        Query the database for rows.
        """
        cursor = cls._get_cursor()
        statement, parameters = cls._prepare_statement(parameters, "SELECT COUNT(1)")
        cursor.execute(statement, parameters)

        return cursor.fetchone()[0]

    @classmethod
    def find(cls, **parameters):
        """
        Query the database for rows.
        """
        cursor = cls._get_cursor()
        statement, parameters = cls._prepare_statement(parameters)
        cursor.execute(statement, parameters)

        for id, data in cursor:
            loaded_dict = json.loads(data)
            obj = cls._unmarshal(loaded_dict)
            obj.id = id
            yield obj

    @classmethod
    def all(cls):
        return cls.find()

    @classmethod
    def initialize(cls):
        """
        Create the necessary tables in the database.
        """
        cursor = cls._get_cursor()
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS %s ( "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "data" JSON);"""
            % cls.__name__.lower()
        )
        cursor.execute(
            """CREATE UNIQUE INDEX IF NOT EXISTS "g_%s_id_index" on %s (id ASC)"""
            % (cls.__name__.lower(), cls.__name__.lower())
        )

        for index in cls.Meta.indexes:
            statement = """CREATE INDEX IF NOT EXISTS "u_%s_index" ON %s (%s);""" % (
                "__".join(index),
                cls.__name__.lower(),
                ", ".join("json_extract(data, '$.%s')" % field for field in index),
            )
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
        self.id = None
        self.__dict__.update(kwargs)

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

    def save(self, commit=True):
        """
        Persist an object to the database.
        """
        cursor = self._get_cursor()

        # Temporarily delete the id so it doesn't get stored, if it exists.
        object_id = self.__dict__.pop("id", None)

        if object_id is None:
            statement = (
                """INSERT INTO %s ("data") VALUES (?)"""
                % self.__class__.__name__.lower()
            )
            cursor.execute(statement, (json.dumps(self.__dict__),))
            new_id = cursor.lastrowid
            self.id = new_id
        else:
            statement = (
                """UPDATE %s SET "data" = ? WHERE "id" = ?"""
                % self.__class__.__name__.lower()
            )
            cursor.execute(statement, (json.dumps(self.__dict__), object_id))

            # Restore the id.
            self.id = object_id

        if commit:
            self.commit()

    def delete(self, commit=True):
        """
        Delete an object from the database.
        """
        cursor = self._get_cursor()
        # Get the name of the main table.
        table_name = self.__class__.__name__.lower()

        # And delete the rows from all of them.
        statement = """DELETE FROM %s WHERE "id" == ?""" % table_name
        cursor.execute(statement, (self.id,))

        if commit:
            self.commit()

    def __str__(self) -> str:
        d = self.__dict__
        d.pop("id", None)
        id = getattr(self, "id", None)
        return "<%s (%s): %s>" % (self.__class__.__name__, id, self.__dict__)

    def __repr__(self) -> str:
        return str(self)

    class Meta:
        connection = None
        indexes = ()
