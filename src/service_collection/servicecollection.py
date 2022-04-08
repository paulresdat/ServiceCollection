import argparse
import inspect
import copy
import enum
import os
import json
import re
from abc import ABCMeta, abstractmethod
from collections.abc import Mapping
from argparse import Namespace
from tkinter import ANCHOR
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Type, TypeVar, Union, cast

from .serviceconfiguration import Configuration, ConfigurationContext, ConfigurationSection

T = TypeVar("T")


class IServiceProvider(metaclass=ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass: Any):
        return (
            hasattr(subclass, 'get_service') and callable(subclass.get_service)
            or NotImplemented
        )

    @abstractmethod
    def get_service(self, class_type: Type[T]) -> T:
        raise NotImplementedError


class IServiceCollection(metaclass=ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass: Any):
        return (
            hasattr(subclass, 'configure') and callable(subclass.configure) and
            hasattr(subclass, 'singletons') and callable(subclass.singletons) and
            hasattr(subclass, 'singleton') and callable(subclass.singleton) and
            hasattr(subclass, 'transients') and callable(subclass.transients) and
            hasattr(subclass, 'transient') and callable(subclass.transient) and
            hasattr(subclass, 'build_service_provider') and callable(subclass.build_service_provider)
            or NotImplemented
        )

    @abstractmethod
    def configure(
        self,
        class_type: type,
        mapped_properties: Union[argparse.Namespace, ConfigurationContext, ConfigurationSection, Dict[str, Any]]
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def singletons(
        self,
        tinterfaces: list[Union[type, list[type]]]
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def singleton(
        self,
        tinterface: type,
        tconcrete: Optional[type] = None,
        instance: Any = None,
        constructor_args: Optional[Union[List[Any], Tuple[Any]]] = []
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def transients(self, tinterfaces: list[Union[type, list[type]]]) -> None:
        raise NotImplementedError

    @abstractmethod
    def transient(
        self,
        tinterface: type,
        tconcrete: Optional[type] = None,
        construction: Optional[Union[List[Any], Tuple[Any], Callable[[], None]]] = None
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def build_service_provider(self) -> IServiceProvider:
        raise NotImplementedError


class ServiceCollection(object):
    def __new__(cls):
        raise TypeError('Service Collection is a static class, you must access a new instance of the service collection by invoking the static method `instance`')

    @staticmethod
    def instance(symbol_table: Dict[str, Any], logging: bool = False, logger: Any = None) -> IServiceCollection:
        return _PrivateServiceCollection(symbol_table, logging, logger)


class _PrivateServiceCollection(IServiceCollection):
    def __init__(self, _parent_globals: Dict[str, Any], logging: bool = False, logger: Any = None):
        self.__fully_registered: Dict[str, Dict[str, Any]] = {}
        self.__service_collection: Dict[str, Dict[str, Any]] = {}
        self.__log = logger
        self.__logging = logging
        self.__globals = _parent_globals

    def configure(
        self,
        class_type: type,
        mapped_properties: Union[argparse.Namespace, ConfigurationContext, ConfigurationSection, Dict[Any, Any]]
    ):
        if inspect.isclass(class_type):
            configure = Configuration(self.__globals, class_type, mapped_properties)
            self.__service_collection[class_type.__name__] = {
                'type': 'transient',
                'instance_type': class_type,
                'constructor_args': [],
                'lambda': lambda: configure.retrieve_instance()
            }
        else:
            raise RuntimeError('Class type must be a type for configuration')

    def singletons(self, tinterfaces: list[Union[type, list[type]]]):
        for x in tinterfaces:
            if type(x) is list:
                if len(x) == 1:
                    self.singleton(x[0])
                elif len(x) == 2:
                    self.singleton(x[0], x[1])
                else:
                    raise RuntimeError("The `singletons` method only accepts a list of types, or a list of interface to type matching")
            else:
                if type(x) is type:
                    self.singleton(x)
                else:
                    raise RuntimeError("unknown type given")

    def singleton(
        self,
        tinterface: type,
        tconcrete: Optional[type] = None,
        instance: Any = None,
        constructor_args: Optional[Union[List[Any], Tuple[Any]]] = []
    ) -> None:
        if inspect.isclass(tinterface):
            # the first way is where everything after the tinterface is None, mapping a concrete explicitly
            c_type = str(tinterface.__name__)
            if tconcrete is None and instance is None:
                args = self.__prepare_constructor_args(tinterface, constructor_args)
                self.__service_collection[c_type] = {
                    'type': 'singleton',
                    'instance_type': tinterface,
                    'constructor_args': args
                }
            # the next way is to map from an interface to a concrete
            elif tconcrete is not None and inspect.isclass(tconcrete) and instance is None:
                if issubclass(tconcrete, tinterface):
                    args = self.__prepare_constructor_args(tconcrete, constructor_args)
                    self.__service_collection[c_type] = {
                        'type': 'singleton',
                        'instance_type': tconcrete,
                        'constructor_args': args
                    }
                else:
                    raise RuntimeError((
                        "The concrete type specified is not a subclass of the interface.  " +
                        "Please consult documentation on abstract/interface design in python.  Examples exist for this github repo."))
            elif instance is not None:
                if isinstance(instance, tinterface):
                    args = self.__prepare_constructor_args((tconcrete if tconcrete is not None else tinterface), constructor_args)
                    self.__fully_registered[c_type] = {
                        'type': 'singleton',
                        'instance': instance,
                        'constructor_args': args
                    }
                elif callable(instance) and instance.__name__ == '<lambda>':
                    # here we are expecting the instance in a lambda function
                    # TODO - analysis on whether an instance check should be performed
                    # on the return object.  I'm thinking not at this time, but may
                    # be desired to be more restrictive
                    self.__fully_registered[c_type] = {
                        'type': 'singleton',
                        'instance': instance()
                    }
                else:
                    raise RuntimeError('Uknown instance type supplied: expecting either an instance of the interface or a lambda')
            else:
                raise RuntimeError('Unknown configuration found for registering a singleton')
        elif type(tinterface) is not type:
            # we have already created instance, just register directly
            self.__fully_registered[tinterface.__name__] = {
                'type': 'singleton',
                'instance': tinterface,
            }
            return

    def transients(
        self,
        tinterfaces: list[Union[type, list[type]]]
    ):
        for x in tinterfaces:
            if type(x) is list:
                if len(x) == 1:
                    self.transient(x[0])
                elif len(x) == 2:
                    self.transient(x[0], x[1])
                else:
                    raise RuntimeError("Invalid number of arguments specified for list of transients")
            else:
                if type(x) is type:
                    self.transient(x)
                else:
                    raise RuntimeError("Invalid argument specified for transient registration")

    def transient(
        self,
        tinterface: type,
        tconcrete: Optional[type] = None,
        construction: Optional[Union[List[Any], Tuple[Any], Callable[[], None]]] = None
    ):
        if inspect.isclass(tinterface):
            c_type = str(tinterface.__name__)
            if inspect.isclass(tconcrete) and construction is not None:
                if callable(construction) and construction.__name__ == '<lambda>':
                    # a registered transient is passed through from a lambda function
                    # register it as lambda called each time the service is fetched
                    self.__service_collection[c_type] = {
                        'type': 'transient',
                        'instance_type': tconcrete,
                        'constructor_args': [],
                        'lambda': construction,
                    }
                else:
                    # TODO - finish this
                    raise RuntimeError('Unknown configuration for concrete type at this time')
            elif inspect.isclass(tconcrete):
                args = self.__prepare_constructor_args(tconcrete, cast(Union[List[Any], Tuple[Any]], construction))
                self.__service_collection[c_type] = {
                    'type': 'transient',
                    'instance_type': tconcrete,
                    'constructor_args': args,
                    'lambda': False,
                }
            else:
                # otherwise it's a bread and butter transient registration
                args = self.__prepare_constructor_args(tinterface, cast(Union[List[Any], Tuple[Any]], construction))
                self.__service_collection[c_type] = {
                    'type': 'transient',
                    'instance_type': tinterface,
                    'constructor_args': args,
                    'lambda': False,
                }
        else:
            raise RuntimeError('unknown type to register as a transient service: expected class type')

    def register_services(
        self,
        service_collection: Dict[str, Dict[str, Any]],
        fully_registered: Dict[str, Dict[str, Any]]
    ):
        self.__service_collection = service_collection
        self.__fully_registered = fully_registered

    def build_service_provider(self):
        return ServiceProvider(self.__set_collection())

    def fetch_service(self, service: Type[T]) -> T:
        assert service is not None
        service_type_as_string = service.__name__
        self.log("Fetching service: " + str(service_type_as_string))
        try:
            if service_type_as_string not in self.__fully_registered.keys():
                # it could be a transient which will always be in this condition
                return self.__construct_service(service_type_as_string)
            else:
                return self.__fully_registered[service_type_as_string]['instance']
        except Exception as e:
            print("Error in fetching service: " + str(service_type_as_string))
            raise e

    def __prepare_constructor_args(
        self,
        class_type: type,
        constructed_args: Optional[Union[List[Any], Tuple[Any]]] = None
    ):
        # first through inspection find the number of arguments
        args = inspect.signature(class_type.__init__)
        params = args.parameters
        length_of_dependencies = len(params) - 1
        # put ordered dict into a list
        params_list: List[Any] = []
        for x in params:
            if x == 'self':
                continue
            p = params[x]
            params_list.append([x, p])

        type_list: List[Dict[str, Any]] = []
        if (
            constructed_args is None or
            (
                (
                    type(constructed_args) is list or
                    type(constructed_args) is tuple
                ) and
                len(constructed_args) == 0
            )
        ):
            # use from the argument list
            for param in params_list:
                annotation = param[1].annotation
                if type(annotation) == str:
                    # if type hinting was done with __future__ used, then the class is represented as a string
                    if self.__globals is None:
                        raise RuntimeError('For automagical type resolution, the calling file globals is required.  ie: ServiceCollection(globals())')
                    annotation = eval(annotation, self.__globals, locals())
                type_list.append({
                    'type': 'class',
                    'arg': annotation
                })
        elif (
            (
                type(constructed_args) is list or
                type(constructed_args) is tuple
            ) and
            len(constructed_args) == length_of_dependencies
        ):
            for x in constructed_args:
                # if built in types
                # TODO - need to analyze this and come up with a better name
                checker: Any = x
                if type(checker) == str or type(checker) == int or type(checker) == float:
                    type_list.append({'type': 'in_built', 'arg': checker})
                elif callable(checker) and checker.__name__ == '<lambda>':
                    type_list.append({'type': 'lambda', 'arg': checker})
                elif inspect.isclass(x):
                    type_list.append({'type': 'class', 'arg': checker})
                else:
                    type_list.append({'type': 'raw', 'arg': checker})
        else:
            # we have something more complex here
            raise RuntimeError('There is an issue where the dependency was not registered with the correct amount of arguments: ' + class_type.__name__)

        # print(type_list)
        return type_list

    def __set_collection(self) -> '_PrivateServiceCollection':
        svc_collection = copy.deepcopy(self.__service_collection)
        svc_fully_formed = copy.deepcopy(self.__fully_registered)
        sc = _PrivateServiceCollection(self.__globals, self.__logging, self.__log)
        sc.register_services(svc_collection, svc_fully_formed)
        return sc

    def __construct_service(self, service_as_string: str) -> Any:
        self.log("Forming service: " + service_as_string)
        tmp = self.__service_collection[service_as_string]
        if tmp['type'] == 'singleton':
            cl = tmp['instance_type']
            if len(tmp['constructor_args']) > 0:
                args_to_pass = self.__get_constructor_args(tmp['constructor_args'])
                try:
                    ins = cl(*args_to_pass)
                except Exception as e:
                    self.log("An error ocurred registering service: " + service_as_string, critical=True)
                    self.log(e.args, True)
                    raise e
            else:
                ins = cl()
            self.__fully_registered[service_as_string] = {'type': 'singleton', 'instance': ins}
            return ins
        elif tmp['type'] == 'transient':
            cl = tmp['instance_type']
            if tmp['lambda'] is not False:
                return tmp['lambda']()
            if len(tmp['constructor_args']) > 0:
                args_to_pass = self.__get_constructor_args(tmp['constructor_args'])
                return cl(*args_to_pass)
            else:
                return cl()

    def __get_constructor_args(self, constructor_args: List[Any]):
        all_args: List[Any] = []
        for arg in constructor_args:
            if arg['type'] == 'class':
                service = self.fetch_service(arg['arg'])
                all_args.append(service)
            else:
                all_args.append(arg['arg'])
        return all_args

    def log(self, message: Any, critical: Optional[bool] = False) -> None:
        if self.__log is None and (self.__logging is True or critical is True):
            print(message)
        elif self.__log is not None:
            self.__log.debug(message)


class ServiceProvider(IServiceProvider):
    def __init__(self, service_collection: _PrivateServiceCollection):
        self.__service_collection = service_collection

    def get_service(self, class_type: Type[T]) -> T:
        assert class_type is not None
        type_: T = self.__service_collection.fetch_service(class_type)
        return type_
