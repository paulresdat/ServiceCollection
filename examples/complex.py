from __future__ import annotations
from asyncio.events import AbstractServer
from typing import TYPE_CHECKING, Any
from abc import ABCMeta, abstractmethod

from servicecollection import ServiceCollection


class ModelInterface(metaclass=ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (
            hasattr(subclass, 'set') and callable(subclass.set) and
            hasattr(subclass, 'save') and callable(subclass.save) and
            hasattr(subclass, 'json_load') and callable(subclass.json_load) and
            # hasattr(subclass, 'dict_load') and callable(subclass.dict_load) and
            hasattr(subclass, 'get_keys') and callable(subclass.get_keys) and
            hasattr(subclass, 'get_values') and callable(subclass.get_values) and 
            hasattr(subclass, 'get_table_name') and callable(subclass.get_table_name) and
            hasattr(subclass, 'get_key_values') and callable(subclass.get_key_values)
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
    def save(self, sql: ISqlInterface):
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


class ISqlInterface(metaclass=ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (
            hasattr(subclass, 'update') and callable(subclass.update) and
            hasattr(subclass, 'sql') and callable(subclass.sql)
            or NotImplemented
        )

    @abstractmethod
    def insert(self, model: ModelAbstract) -> ISqlInterface:
        raise NotImplemented

    @abstractmethod
    def update(self, model: ModelAbstract) -> ISqlInterface:
        raise NotImplemented

    @abstractmethod
    def sql(self) -> str:
        raise NotImplemented

class Sql(ISqlInterface):
    def __init__(self):
        """ FAKE SQL Object"""
        pass

    def insert(self, model: ModelAbstract) -> ISqlInterface:
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

    def update(self, model: ModelAbstract) -> ISqlInterface:
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

    def save(self, sql: ISqlInterface) -> int:
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
    def __subclasshook__(cls, subclass):
        return (
            hasattr(subclass, 'id') and
            hasattr(subclass, 'name') and
            hasattr(subclass, 'data_model') or
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



def main():
    # TODO - add Interface in place of Concrete for fetching
    sc = ServiceCollection(globals())
    sc.transient(SuperModel)
    sc.singleton(Sql)
    sp = sc.build_service_provider()
    sql = sp.get_service(Sql)
    
    new_super_model: SuperModel = sp.get_service(SuperModel)
    # s.id = 1
    new_super_model.name = "hi"
    new_super_model.save(sql)


if __name__ == '__main__':
    main()
