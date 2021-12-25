import argparse
import sys
from src.service_collection.servicecollection import ConfigurationContext, ServiceCollection, ServiceProvider


class ConfigureClass(object):
    name: str

    def __init__(self):
        self.__name = None
        pass

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, val: str):
        self.__name = val

def parse_args(sys_args=None):
    parser = argparse.ArgumentParser(description='Argument parsing for configuration tests')
    parser.add_argument('--name', type=str, help='argument to specify table-name')
    args = parser.parse_args(sys_args if sys_args else ['--help'])
    return args

def main():
    import os
    os.environ["TEST_SVC"] = "target1"
    ctxt = ConfigurationContext("tests/settings.json", overriden_target_context_os_env_name="TEST_SVC")
    js = ctxt.file_as_dict
    print(js)


def test1():
    # best practice
    # args = parse_args(sys.argv[1:])
    # args = parse_args(['--name', 'hello2'])
    sc = ServiceCollection(globals())
    sc.configure(ConfigureClass, {
        'name': 'hello',
    })
    # sc.configure(ConfigureClass, args)
    sp: ServiceProvider = sc.build_service_provider()
    conf: ConfigureClass = sp.get_service(ConfigureClass)


if __name__ == '__main__':
    main()
