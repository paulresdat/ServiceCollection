import enum
import inspect
import json
import os
import re
from abc import ABCMeta, abstractmethod
from argparse import Namespace
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple, cast, Union


class ServiceCollectionConst(enum.Enum):
    OS_ENV_NAME = "SERVICE_COLLECTION_ENV"


class IConfigurationObject(metaclass=ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass: Any):
        return (
            hasattr(subclass, 'transform_to_dict') and callable(subclass.transform_to_dict)
            or NotImplemented
        )

    @abstractmethod
    def transform_to_dict(self) -> dict:
        raise NotImplementedError()


class BaseConfigurationObject(IConfigurationObject):
    def transform_to_dict(self):
        d = dict()
        for k in self.__annotations__.keys():
            val = getattr(self, k)
            if isinstance(val, IConfigurationObject):
                d[k] = val.transform_to_dict()
            else:
                d[k] = val
        return d


class ConfigurationSection(object):
    def __init__(self, settings_as_dict: Optional[Dict[str, Any]]):
        self.__settings = settings_as_dict

    @property
    def settings(self):
        return self.__settings


class IJsonLoader(metaclass=ABCMeta):
    @classmethod
    def __subclasshook__(self, subclass: Any):
        return (
            hasattr(subclass, 'loads') and callable(subclass.loads) and
            hasattr(subclass, 'dumps') and callable(subclass.dumps)
            or NotImplemented
        )

    @abstractmethod
    def loads(self, data: str):
        raise NotImplementedError()

    @abstractmethod
    def dumps(self, data: Any):
        raise NotImplementedError()


class ConfigurationContext(Mapping[str, Any]):
    def __init__(
        self,
        json_file: str,
        target_context: Optional[str] = None,
        target_context_os_env_name: Optional[str] = None,
        json_loader: IJsonLoader = None
    ):
        # declare all private properties
        self.__file: Optional[Dict[str, Any]] = None
        self.__json_file: str = json_file
        self.__target_context: Optional[str] = target_context
        self.__target_context_os_env: Optional[str] = None
        self.__json_loader = json_loader
        # self.__file_as_dict: Dict[str, Any] = {}
        # end declaration
        if target_context_os_env_name is not None:
            self.__target_context_os_env = target_context_os_env_name
        else:
            self.__target_context_os_env = str(ServiceCollectionConst.OS_ENV_NAME.value)
        if target_context is None:
            # get the target context from the os name
            self.__target_context = os.getenv(self.__target_context_os_env)

    def keys(self):
        return self.__file_as_dict.keys()

    def __getitem__(self, key: Any):
        return self.get_section(str(key)).settings

    def __iter__(self):
        if self.__file_as_dict is None:
            return iter({})
        return iter(cast(Iterable[Any], self.__file_as_dict))

    def __len__(self):
        return len(self.keys())

    @property
    def __file_as_dict(self) -> Dict[str, Any]:
        if self.__file is None:
            self.__fetch_file()
        return self.__file if self.__file is not None else {}

    def define_os_env_name(self, environment_variable_name: str) -> None:
        self.__target_context_os_env = environment_variable_name
        self.__target_context = os.getenv(self.__target_context_os_env)

    def get_section(self, section: str) -> ConfigurationSection:
        args = section.split(":")
        _f = self.__get_file()
        current_pos = ({} if _f is None else _f)
        for a in args:
            # drill into it
            if a in current_pos.keys():
                current_pos = current_pos[a]
            else:
                return ConfigurationSection(None)
        return ConfigurationSection(current_pos)

    def __get_file(self) -> Optional[Dict[Any, Any]]:
        if self.__file is None:
            self.__fetch_file()
        return self.__file

    def __load_s(self, file_name: str):
        # no try catch! let it fail if there's an issue
        with open(file_name, 'r') as f:
            lines = f.readlines()
            if self.__json_loader is not None:
                return self.__json_loader.loads("\n".join(lines))
            return json.loads("\n".join(lines))

    def __fetch_file(self):
        self.__file = self.__load_s(self.__json_file)
        if self.__target_context is not None and self.__target_context != "":
            # there is a file to assimilate
            tmp_fn = self.__json_file.split(".")
            last = tmp_fn.pop()
            tmp_fn.append(self.__target_context)
            tmp_fn.append(last)
            target_file = ".".join(tmp_fn)
            file_ = self.__load_s(target_file)
            self.__merge_dicts(file_, self.__file)

    def __merge_dicts(self, source_file: Dict[str, Any], destination_file: Dict[str, Any]):
        dest_keys = destination_file.keys()
        for key in source_file.keys():
            if key in dest_keys and type(destination_file[key]) is dict:
                # be careful not to overwrite, rather append attributes if key doesn't exist
                self.__merge_dicts(source_file[key], destination_file[key])
            else:
                destination_file[key] = source_file[key]


class Configuration():
    def __init__(
        self,
        _parent_globals: Dict[str, Any],
        class_type: type,
        mapped_properties: Union[Namespace, ConfigurationContext, ConfigurationSection, Dict[Any, Any]]
    ):
        json_data: Union[Namespace, Dict[str, Any]] = {}
        if type(mapped_properties) is dict:
            json_data = mapped_properties
        elif type(mapped_properties) is Namespace:
            # automatic support for argparse is enabled
            json_data = mapped_properties
        elif isinstance(mapped_properties, (ConfigurationContext,)):
            # mapping from configuration context or section
            _f = {**mapped_properties}
            json_data = _f if _f is not None else {}
        elif isinstance(mapped_properties, (ConfigurationSection,)):
            # mapping
            json_data = mapped_properties.settings if mapped_properties.settings is not None else {}
        else:
            print("UNSUPPORTED TYPE FOR CONFIGURATION: " + str(type(mapped_properties)))
            exit()
        self.class_type = class_type
        self.json_data = json_data
        self.__globals = _parent_globals

    def retrieve_instance(self):
        members = inspect.getmembers(self.class_type)
        annotations = self.__get_annotations(members)
        instance = self.__map_conf(self.json_data, self.class_type, annotations)
        return instance

    def __map_conf(self, conf: Union[Dict[str, Any], Namespace], object_to_map: type, mapper_info: Dict[str, Dict[str, Any]]):
        o = object_to_map()
        mapped_conf = {}
        if type(conf) is Namespace:
            mapped_conf = vars(conf)
        elif type(conf) is dict:
            mapped_conf: Dict[str, Any] = conf
        else:
            raise RuntimeError('type not supported to map when mapping configurations in the service collection')

        for x in mapped_conf:
            name = self.__scrub_name(x)
            val = mapped_conf[x]
            if name in mapper_info.keys():
                if mapper_info[name]['inner_annotations'] is not None:
                    mapped = self.__map_conf(val, mapper_info[name]['type'], mapper_info[name]['inner_annotations'])
                else:
                    mapped = val
                setattr(o, mapper_info[name]['name'], mapped)

        # put the None in where there is no mapping
        stripped_keys = [self.__scrub_name(x.strip()) for x in mapped_conf.keys()]
        for x in mapper_info.keys():
            if x not in stripped_keys:
                setattr(o, mapper_info[x]['name'], None)

        return o

    def __scrub_name(self, name: str) -> str:
        return re.sub('[^A-Za-z0-9_]', '', name).lower()

    def __get_annotations(self, members: List[Tuple[str, Any]]):
        annotations = None
        for x in members:
            if x[0] == '__annotations__':
                annotations = x[1]
                break
        if annotations is None:
            raise RuntimeError((
                "There are no known mapped properties of your configuration class. " +
                "You need to globally specify the property.  Please consult documentation. "
            ))

        cl_atts: Dict[str, Dict[str, Any]] = {}
        for x in annotations:
            cl_name = self.__scrub_name(x)
            try:
                # weird typing type workaround?  Needs more analysis
                # print(x)
                alias_name = type(annotations[x]).__name__
                if (alias_name == "_SpecialGenericAlias" or alias_name == "_GenericAlias"):
                    n = annotations[x].__dict__['_name']
                elif hasattr(annotations[x], '__name__'):
                    n = annotations[x].__name__
                else:
                    if type(annotations[x]) is str:
                        n = annotations[x]
                    else:
                        raise RuntimeError("Unsupported annotation type: " + x)
                cl_type = eval(n, self.__globals, locals())
            except TypeError as e:
                print("A type error occurred in your configuration: " + cl_name + " : " + str(annotations[x]))
                raise e
            except Exception as e:
                # TODO - this needs to be figured out and a better error message needs to be here
                print("A general error has occurred in your configuration: " + cl_name + " : " + str(annotations[x]))
                print(e.args)
                raise e
                exit()
            inner_annotations = None
            # TODO - figure out a more elegant way of doing this
            if (
                type(cl_type).__name__ != "_SpecialGenericAlias" and
                cl_type.__name__ not in ['str', 'float', 'int', 'list', 'dict', 'tuple', 'bool', 'typing.List']
            ):
                members = inspect.getmembers(cl_type)
                try:
                    inner_annotations = self.__get_annotations(members)
                except Exception as e:
                    print("There was an issue retrieving annotations for " + x + " with type " + str(cl_type.__name__))
                    raise e
            cl_atts[cl_name] = {
                'name': x,
                'type': cl_type,
                'inner_annotations': inner_annotations
            }
        return cl_atts
