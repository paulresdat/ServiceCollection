from __future__ import annotations
from typing import Any, Dict, List
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
    def __subclasshook__(cls, subclass: Any):
        return (
            hasattr(subclass, 'set') and callable(subclass.set) and
            hasattr(subclass, 'save') and callable(subclass.save) and
            hasattr(subclass, 'json_load') and callable(subclass.json_load) and
            hasattr(subclass, 'get_keys') and callable(subclass.get_keys) and
            hasattr(subclass, 'get_values') and callable(subclass.get_values) and 
            hasattr(subclass, 'get_table_name') and callable(subclass.get_table_name) and
            hasattr(subclass, 'get_key_values') and callable(subclass.get_key_values)
            or NotImplemented
        )

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """ set the internal data structure """
        raise NotImplementedError

    @abstractmethod
    def get(self, key: str) -> Any:
        raise NotImplementedError

    @abstractmethod
    def save(self, sql: ISql) -> int:
        """ save loaded data """
        raise NotImplementedError

    @abstractmethod
    def get_identity_key(self) -> str:
        """ get the registered identity key """
        raise NotImplementedError

    @abstractmethod
    def json_load(self, json: str) -> None:
        """ load the model via a json string """
        raise NotImplementedError

    # @abstractmethod
    # def dict_load(self, mapped_data: dict):
    #     """ load the model by a dictionary """
    #     raise NotImplemented

    @abstractmethod
    def get_keys(self) -> List[str]:
        """ get keys """
        raise NotImplementedError

    @abstractmethod
    def get_values(self) -> List[Any]:
        """ get values """
        raise NotImplementedError

    @abstractmethod
    def get_key_values(self) -> Dict[str, Any]:
        """ get key value dictionary """
        raise NotImplementedError

    @abstractmethod
    def get_table_name(self) -> str:
        """ get table name """
        raise NotImplementedError


class ISql(metaclass=ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass: Any):
        return (
            hasattr(subclass, 'update') and callable(subclass.update) and
            hasattr(subclass, 'sql') and callable(subclass.sql)
            or NotImplemented
        )

    @abstractmethod
    def insert(self, model: ModelAbstract) -> ISql:
        raise NotImplementedError

    @abstractmethod
    def update(self, model: ModelAbstract) -> ISql:
        raise NotImplementedError

    @abstractmethod
    def sql(self) -> str:
        raise NotImplementedError


class Sql(ISql):
    def __init__(self):
        """ FAKE SQL Object"""
        pass

    def insert(self, model: ModelAbstract) -> ISql:
        identity = model.get_identity_key()
        keys: List[Any] = []
        vals: List[Any] = []
        for k, v in model.get_key_values().items():
            if k != identity:
                keys.append(k)
                vals.append(v)

        self.__sql = "INSERT INTO " + model.get_table_name() + " ("
        self.__sql += ", ".join(keys) + ") VALUES ('"
        self.__sql += "', '".join([str(x) for x in vals]) + "')"
        return self

    def update(self, model: ModelAbstract) -> ISql:
        key_values = model.get_key_values()
        self.__sql = "UPDATE " + model.get_table_name() + " SET "
        vals: List[Any] = []
        for k, v in key_values.items():
            vals.append(k + " = '" + str(v) + "'")
        self.__sql += ", ".join([str(x) for x in vals])
        return self

    def sql(self) -> str:
        return self.__sql


class ModelAbstract(ModelInterface):
    def __init__(self, table_name: str, identity_column_name: str, column_information: Dict[str, Any]):
        self.__table_name = table_name
        self.__identity_column_name = identity_column_name
        self.__column_information = column_information
        self.__key_values: Dict[str, Any] = {}
        for c in column_information.keys():
            self.__key_values[c] = None

    def set(self, key: str, value: Any) -> None:
        self.__key_values[key] = value

    def get(self, key: str):
        return self.__key_values[key]

    def save(self, sql: ISql) -> int:
        if self.__key_values[self.__identity_column_name] is None:
            sql_ = sql.insert(self).sql()
        else:
            sql_ = sql.update(self).sql()
        print(sql_)
        return 1

    def get_identity_key(self):
        return self.__identity_column_name

    def json_load(self, json: str) -> None:
        pass

    def get_keys(self) -> List[str]:
        """ get keys """
        return [x for x in self.__key_values.keys()]

    def get_values(self) -> List[Any]:
        """ get values """
        return [x for x in self.__key_values.values()]

    def get_key_values(self):
        """ get key value dictionary """
        return self.__key_values

    def get_table_name(self):
        """ get table name """
        return self.__table_name


class ISuperModel(metaclass=ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass: Any):
        return (
            hasattr(subclass, 'id') and
            hasattr(subclass, 'name') and
            hasattr(subclass, 'data_model') or
            NotImplemented
        )

    @property
    @abstractmethod
    def id(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def data_model(self) -> str:
        raise NotImplementedError


class SuperModel(ModelAbstract, ISuperModel):
    def __init__(self):
        super().__init__("SuperModels", "Id", {
            'Id': {'type': int},
            'Name': {'type': str},
            'DataModel': {'type': str}
        })

    @property
    def id(self) -> int:
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
    def __subclasshook__(cls, subclass: Any):
        return (
            hasattr(subclass, 'make_model') and callable(subclass.make_model)
            or NotImplemented
        )

    @abstractmethod
    def make_model(self) -> None:
        raise NotImplementedError


class ModelRepository(IModelRepository):
    def __init__(self, sql: ISql):
        self.__sql = sql

    def make_model(self):
        model = SuperModel()
        model.save(self.__sql)


def main():
    sc = ServiceCollection.instance(globals()) # ServiceCollection(globals())
    sc.singleton(IModelRepository, ModelRepository)
    sc.singleton(ISql, Sql)
    sp = sc.build_service_provider()
    repo: IModelRepository = sp.get_service(IModelRepository)
    print(isinstance(repo, IModelRepository))
    repo.make_model()


if __name__ == '__main__':
    main()
