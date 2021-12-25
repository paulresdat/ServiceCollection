import argparse
import inspect
import copy
import re
import json
import os
import enum
from argparse import Namespace
from typing import List, Union


class ConfigurationSection(object):
    def __init__(self):
        pass


class ServiceCollectionConst(enum.Enum):
    OS_ENV_NAME = "SERVICE_COLLECTION_CONF"


class ConfigurationContext(object):
    def __init__(self, json_file: str, target_context: str = None, overriden_target_context_os_env_name: str = None):
        # declare all private properties
        self.__file: dict = None
        self.__json_file: str = json_file
        self.__target_context: str = target_context
        self.__target_context_os_env: str = None
        # end declaration

        if overriden_target_context_os_env_name is not None:
            self.__target_context_os_env = overriden_target_context_os_env_name
        else:
            self.__target_context_os_env = ServiceCollectionConst.OS_ENV_NAME.value
        if target_context is None:
            # get the target context from the os name
            self.__target_context = os.getenv(self.__target_context_os_env)

    def define_os_env_name(self, environment_variable_name: str) -> None:
        self.__target_context_os_env = environment_variable_name
        self.__target_context = os.getenv(self.__target_context_os_env)

    def get_section(self, section: str):
        args = section.split(":")
        current_pos = self.file_as_dict
        for a in args:
            # drill into it
            if a in current_pos.keys():
                current_pos = current_pos[a]
            else:
                return None
        return current_pos


    @property
    def file_as_dict(self) -> Union[dict,None]:
        if self.__file is None:
            self.__fetch_file()
        return self.__file

    def __load_s(self, file_name: str):
        # no try catch! let it fail if there's an issue
        with open(file_name, 'r') as f:
            lines = f.readlines()
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

    def __merge_dicts(self, source_file: dict, destination_file: dict):
        dest_keys = destination_file.keys()
        for key in source_file.keys():
            if key in dest_keys and type(destination_file[key]) is dict:
                # be careful not to overwrite, rather append attributes if key doesn't exist
                self.__merge_dicts(source_file[key], destination_file[key])
            else:
                destination_file[key] = source_file[key]


class Configuration(object):
    def __init__(self, _parent_globals: dict, class_type, mapped_properties: Union[dict, str]):
        if type(mapped_properties) is dict:
            json_data = mapped_properties
        elif type(mapped_properties) is str:
            with open(mapped_properties, 'r') as f:
                json_str = f.readlines()
                json_data = json.loads("".join(json_str))
        elif type(mapped_properties) is argparse.Namespace:
            # automatic support for argparse is enabled
            json_data = mapped_properties
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

    def __map_conf(self, conf: dict, object_to_map, mapper_info: dict):
        o = object_to_map()
        mapped_conf = None
        if type(conf) == Namespace:
            mapped_conf = vars(conf)
        else:
            mapped_conf = conf

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
        return re.sub('[^A-Za-z0-9]', '', name).lower()

    def __get_annotations(self, members):
        annotations = None
        for x in members:
            if x[0] == '__annotations__':
                annotations = x[1]
                break
        
        if annotations is None:
            raise RuntimeError("There are no known mapped properties of your configuration class.  You need to globally specify the property.  Please consult documentation.")

        cl_atts = {}
        for x in annotations:
            cl_name = self.__scrub_name(x)
            try:
                # weird typing type workaround?  Needs more analysis
                # print(x)
                if (type(annotations[x]).__name__ == "_SpecialGenericAlias"):
                    n = annotations[x].__dict__['_name']
                else:
                    n = annotations[x].__name__
                cl_type = eval(n, self.__globals, locals())
            except TypeError as e:
                print("A type error occurred in your configuration: " + cl_name + " : " + str(annotations[x]))
                raise e
            except Exception as e:
                # TODO - this needs to be figured out and a better error message needs to be here
                print("A general error has occurred in your configuration: " + cl_name + " : " + str(annotations[x]))
                print(e.args)
                exit()
            inner_annotations = None
            # TODO - figure out a more elegant way of doing this
            if type(cl_type).__name__ != "_SpecialGenericAlias" and \
                cl_type.__name__ not in ['str', 'float', 'int', 'list', 'dict', 'tuple', 'bool', 'typing.List']:
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


class ServiceCollection(object):
    def __init__(self, _parent_globals: dict = None, logging=False, logger=None):
        self.__fully_registered = {}
        self.__service_collection = {}
        self.__log = logger
        self.__logging = logging
        self.__globals = _parent_globals

    def configure(self, class_type, mapped_properties: Union[dict, str]):
        if inspect.isclass(class_type):
            # a configuration is always a singelton for right now
            # not sure if it should be in the transient factory pattern right now
            configure = Configuration(self.__globals, class_type, mapped_properties)
            self.__fully_registered[class_type.__name__] = {
                'type': 'singleton',
                'instance': configure.retrieve_instance()
            }
        else:
            raise RuntimeError('Class type must be a type for configuration')

    def singletons(self, t: list):
        for x in t:
            self.singleton(x)

    def singleton(self, t, arg_types=[]):
        if inspect.isclass(t):
            if callable(arg_types) and arg_types.__name__ == '<lambda>':
                # a registered singleton is passed through from a lambda function
                # register it as fully formed
                self.__fully_registered[t.__name__] = {
                    'type': 'singleton',
                    'instance': arg_types()
                }
            else:
                # else, it's a bread and butter singleton registration
                c_type = str(t.__name__)
                args = self.__prepare_constructor_args(t, arg_types)
                self.__service_collection[c_type] = {
                    'type': 'singleton',
                    'instance_type': t,
                    'constructor_args': args
                }
        else:
            # we have already created instance, just register directly
            self.__fully_registered[t.__name__] = {
                'type': 'singleton',
                'instance': t,
            }
            return

    def transients(self, t: list):
        for x in t:
            self.transient(x)

    def transient(self, t, arg_types=[]):
        if inspect.isclass(t):
            c_type = str(t.__name__)
            if callable(arg_types) and arg_types.__name__ == '<lambda>':
                # a registered transient is passed through from a lambda function
                # register it as lambda called each time the service is fetched
                self.__service_collection[c_type] = {
                    'type': 'transient',
                    'instance_type': t,
                    'constructor_args': [],
                    'lambda': arg_types,
                }
            else:
                # otherwise it's a bread and butter transient registration
                args = self.__prepare_constructor_args(t, arg_types)
                self.__service_collection[c_type] = {
                    'type': 'transient',
                    'instance_type': t,
                    'constructor_args': args,
                    'lambda': False,
                }
        else:
            raise RuntimeError('unknown type to register as a transient service: expected class type')

    def register_services(self, service_collection, fully_registered):
        self.__service_collection = service_collection
        self.__fully_registered = fully_registered

    def build_service_provider(self):
        return ServiceProvider(self.__set_collection())

    def fetch_service(self, service_type_as_string):
        self.log("Fetching service: " + str(service_type_as_string))
        try:
            if service_type_as_string not in self.__fully_registered.keys():
                service = self.__construct_service(service_type_as_string)
                # it could be a transient which will always be in this condition
                return service
            else:
                return self.__fully_registered[service_type_as_string]['instance']
        except Exception as e:
            print("Error in fetching service: " + str(service_type_as_string))
            raise e

    def log(self, message: str, critical=False):
        if self.__log is None and (self.__logging is True or critical is True):
            print(message)
        elif self.__log is not None:
            self.__log.debug(message)

    def __prepare_constructor_args(self, class_type, constructed_args: List = None):
        # first through inspection find the number of arguments
        args = inspect.signature(class_type.__init__)
        params = args.parameters
        length_of_dependencies = len(params) - 1
        # put ordered dict into a list
        params_list = []
        for x in params:
            if x == 'self':
                continue
            params_list.append([x, params[x]])

        type_list = []
        if constructed_args is None or len(constructed_args) == 0:
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
        elif len(constructed_args) == length_of_dependencies:
            for x in constructed_args:
                # if built in types
                if type(x) == str or type(x) == int:
                    type_list.append({'type': 'in_built', 'arg': x})
                elif callable(x) and x.__name__ == '<lambda>':
                    type_list.append({'type': 'lambda', 'arg': x})
                elif inspect.isclass(x):
                    type_list.append({'type': 'class', 'arg': x})
                else:
                    type_list.append({'type': 'raw', 'arg': x})
        else:
            # we have something more complex here
            raise RuntimeError('There is an issue where the dependency was not registered with the correct amount of arguments: ' + class_type.__name__)

        # print(type_list)
        return type_list

    def __set_collection(self):
        svc_collection = copy.deepcopy(self.__service_collection)
        svc_fully_formed = copy.deepcopy(self.__fully_registered)
        sc = ServiceCollection(self.__logging, self.__log)
        sc.register_services(svc_collection, svc_fully_formed)
        return sc

    def __construct_service(self, service_as_string):
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

    def __get_constructor_args(self, constructor_args):
        all_args = []
        for arg in constructor_args:
            if arg['type'] == 'class':
                type_name = arg['arg'].__name__
                service = self.fetch_service(type_name)
                all_args.append(service)
            else:
                all_args.append(arg['arg'])
        return all_args


class ServiceProvider(object):
    def __init__(self, service_collection: ServiceCollection):
        self.__service_collection = service_collection
        pass

    def get_service(self, class_type):
        class_name = class_type.__name__
        return self.__service_collection.fetch_service(class_name)
