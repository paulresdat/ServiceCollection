from typing import List
import unittest
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


class ConfigureClass2(object):
    def __init__(self):
        self.__name = None
        pass

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, val: str):
        self.__name = val


# try without getter setters
class ComplexConfig(object):
    name: str
    def __init__(self):
        self.name = None


class ComplexOneConfig(object):
    term1: str
    term2: str
    def __init__(self):
        pass

class ComplexObjectConfig(object):
    complex1: ComplexOneConfig
    value1: bool
    value2: int
    value3: List
    def __init__(self):
        pass


class FullRecursiveConfiguration(object):
    name: str
    complex: ComplexConfig
    complex_object: ComplexObjectConfig
    def __init__(self):
        pass

class ConfigurationTests(unittest.TestCase):
    def setUp(self):
        # sc = ServiceCollection(globals())
        # sc.configure()
        # sc.singletons([])
        pass

    def test_that_configure_can_take_a_dict_value(self):
        sc = ServiceCollection(globals())
        sc.configure(ConfigureClass, {
            'name': 'hello',
        })
        sp: ServiceProvider = sc.build_service_provider()
        conf: ConfigureClass = sp.get_service(ConfigureClass)
        self.assertEqual(conf.name, "hello")

    def test_that_a_bad_configuration_class_throws_an_exception(self):
        sc = ServiceCollection(globals())
        with self.assertRaises(
            RuntimeError,
            msg="There are no known mapped properties of your configuration class.  " +\
                "You need to globally specify the property.  Please consult documentation."):
            sc.configure(ConfigureClass2, {
                'name': 'hello'
            })

    def test_can_recursively_create_a_complex_configuration_object(self):
        """ deep check for completely transformed nested objects """
        sc = ServiceCollection(globals())
        ctxt = ConfigurationContext("tests/settings.json")
        sc.configure(FullRecursiveConfiguration, ctxt.file_as_dict)
        sp: ServiceProvider = sc.build_service_provider()
        fc: FullRecursiveConfiguration = sp.get_service(FullRecursiveConfiguration)
        
        self.assertEqual(type(fc.complex_object), ComplexObjectConfig)
        self.assertEqual(type(fc.complex_object.complex1), ComplexOneConfig)
        self.assertEqual(type(fc.complex), ComplexConfig)
        self.assertEqual(type(fc.name), str)
        
        self.assertEqual(fc.name, "hello")
        self.assertEqual(fc.complex.name, "hello2")
        self.assertEqual(fc.complex_object.complex1.term1, "one")
        self.assertEqual(fc.complex_object.complex1.term2, "two")
        self.assertEqual(fc.complex_object.value1, True)
        self.assertEqual(fc.complex_object.value2, 1)
        self.assertListEqual(fc.complex_object.value3, [1, 2, 3, 4])

        sc = ServiceCollection(globals())
        ctxt = ConfigurationContext("tests/settings.json", "target1")
        sc.configure(FullRecursiveConfiguration, ctxt.file_as_dict)
        sp: ServiceProvider = sc.build_service_provider()
        fc: FullRecursiveConfiguration = sp.get_service(FullRecursiveConfiguration)

        self.assertEqual(fc.name, "hello")
        self.assertEqual(fc.complex.name, "hello2")
        self.assertEqual(fc.complex_object.complex1.term1, "one")
        self.assertEqual(fc.complex_object.complex1.term2, "two")
        self.assertEqual(fc.complex_object.value1, False)
        self.assertEqual(fc.complex_object.value2, 1)
        self.assertListEqual(fc.complex_object.value3, [6, 7, 8, 9, 10])

