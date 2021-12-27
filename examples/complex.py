from __future__ import annotations
from typing import Any
from abc import ABCMeta, abstractmethod

from servicecollection import ServiceCollection

# This example shows a higher level of abstraction and interface design that the service collection
# would be agnostic to.  You can use metaclasses and interface design to implement complex logic
# and use the concrete class to fetch it from the service.  You can even use multiple inheritance
# and it should still work as expected.

# The example is a hypothetical situation where you need an abstract model to keep track of changes
# programmatically so that middleware objects that use the abstract implementation can automate
# tasks without knowing the actual concrete type of the parent class.  In essence this file also
# illustrates when you would want to use custom meta classes, abstract implementations you would
# like enforced and interface design in Python.

class ModelInterface(metaclass=ABCMeta):
    @classmethod
    def __subclasshook__(cls):
        return (
            hasattr(cls, 'set') and callable(cls.set) and
            hasattr(cls, 'save') and callable(cls.save) and
            hasattr(cls, 'json_load') and callable(cls.json_load) and
            hasattr(cls, 'get_keys') and callable(cls.get_keys) and
            hasattr(cls, 'get_values') and callable(cls.get_values) and 
            hasattr(cls, 'get_table_name') and callable(cls.get_table_name) and
            hasattr(cls, 'get_key_values') and callable(cls.get_key_values)
            or NotImplemented
        )

    @abstractmethod
    def set(self, key: str, value: Any):
        """ set the internal data structure """
        raise NotImplemented

    @abstractmethod
    def get(self, key: str):
        raise NotImplemented

    @abstractmethod
    def save(self, sql: ISql):
        """ save loaded data """
        raise NotImplemented

    @abstractmethod
    def get_identity_key(self):
        """ get the registered identity key """
        raise NotImplemented

    @abstractmethod
    def json_load(self, json: str):
        """ load the model via a json string """
        raise NotImplemented

    # @abstractmethod
    # def dict_load(self, mapped_data: dict):
    #     """ load the model by a dictionary """
    #     raise NotImplemented

    @abstractmethod
    def get_keys(self):
        """ get keys """
        raise NotImplemented

    @abstractmethod
    def get_values(self):
        """ get values """
        raise NotImplemented

    @abstractmethod
    def get_key_values(self):
        """ get key value dictionary """
        raise NotImplemented

    @abstractmethod
    def get_table_name(self):
        """ get table name """
        raise NotImplemented


class ISql(metaclass=ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (
            hasattr(cls, 'update') and callable(cls.update) and
            hasattr(cls, 'sql') and callable(cls.sql)
            or NotImplemented
        )

    @abstractmethod
    def insert(self, model: ModelAbstract) -> ISql:
        raise NotImplemented

    @abstractmethod
    def update(self, model: ModelAbstract) -> ISql:
        raise NotImplemented

    @abstractmethod
    def sql(self) -> str:
        raise NotImplemented

class Sql(ISql):
    def __init__(self):
        """ FAKE SQL Object"""
        pass

    def insert(self, model: ModelAbstract) -> ISql:
        identity = model.get_identity_key()
        keys = []
        vals = []
        for k, v in model.get_key_values().items():
            if k != identity:
                keys.append(k)
                vals.append(v)

        self.__sql = "INSERT INTO " + model.get_table_name() + " ("
        self.__sql += ", ".join(keys) + ") VALUES ('"
        self.__sql += "', '".join([str(x) for x in vals]) + "')"
        
        return self

    def update(self, model: ModelAbstract) -> ISql:
        key_values: dict = model.get_key_values()
        self.__sql = "UPDATE " + model.get_table_name() + " SET "
        vals = []
        for k, v in key_values.items():
            vals.append(k + " = '" + str(v) + "'")
        self.__sql += ", ".join([str(x) for x in vals])
        return self

    def sql(self) -> str:
        return self.__sql


class ModelAbstract(ModelInterface):
    def __init__(self, table_name: str, identity_column_name: str, column_information: dict):
        self.__table_name = table_name
        self.__identity_column_name = identity_column_name
        self.__column_information = column_information
        self.__key_values = {}
        for c,d in column_information.items():
            self.__key_values[c] = None

    def set(self, key: str, value: Any):
        self.__key_values[key] = value

    def get(self, key: str):
        return self.__key_values[key]

    def save(self, sql: ISql) -> int:
        if self.__key_values[self.__identity_column_name] is None:
            sql = sql.insert(self).sql()
        else:
            sql = sql.update(self).sql()
        print(sql)
        return 1

    def get_identity_key(self):
        return self.__identity_column_name

    def json_load(self, json_string_data: str):
        pass

    def get_keys(self):
        """ get keys """
        return self.__key_values.keys()

    def get_values(self):
        """ get values """
        return self.__key_values.values()

    def get_key_values(self):
        """ get key value dictionary """
        return self.__key_values

    def get_table_name(self):
        """ get table name """
        return self.__table_name

class ISuperModel(metaclass=ABCMeta):
    @classmethod
    def __subclasshook__(cls):
        return (
            hasattr(cls, 'id') and
            hasattr(cls, 'name') and
            hasattr(cls, 'data_model') or
            NotImplemented
        )

    @abstractmethod
    def id(self):
        raise NotImplemented

    @abstractmethod
    def name(self):
        raise NotImplemented

    @abstractmethod
    def data_model(self):
        raise NotImplemented


class SuperModel(ModelAbstract, ISuperModel):
    def __init__(self):
        super().__init__("SuperModels", "Id", {
            'Id': { 'type': int },
            'Name': { 'type': str },
            'DataModel': { 'type': str }
        })

    @property
    def id(self):
        return self.get('Id')

    @id.setter
    def id(self, val: int):
        self.set('Id', val)

    @property
    def name(self):
        return self.get('Name')

    @name.setter
    def name(self, name: str):
        self.set('Name', name)

    @property
    def data_model(self):
        return self.get('DataModel')

    @data_model.setter
    def data_model(self, model: str):
        return self.set('DataModel', model)


class IModelRepository(metaclass=ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (
            hasattr(cls, 'make_model') and callable(cls.make_model)
            or NotImplemented
        )

    @abstractmethod
    def make_model(self):
        raise NotImplemented


class ModelRepository(IModelRepository):
    def __init__(self, sql: ISql):
        self.__sql = sql

    def make_model(self):
        model = SuperModel()
        model.save(self.__sql)

def main():
    sc = ServiceCollection(globals())
    sc.singleton(IModelRepository, ModelRepository)
    sc.singleton(ISql, Sql)
    sp = sc.build_service_provider()
    repo: IModelRepository = sp.get_service(IModelRepository)
    print(isinstance(repo, IModelRepository))
    repo.make_model()


if __name__ == '__main__':
    main()
