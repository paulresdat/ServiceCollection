from typing import Any, List, Optional
import unittest
from src.service_collection.servicecollection import ConfigurationContext, ServiceCollection


class ConfigureClass(object):
    name: str  # type: ignore

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


class ComplexOneConfig(object):
    term1: str
    term2: str


class ComplexObjectConfig(object):
    complex1: ComplexOneConfig
    value1: bool
    value2: int
    value3: List[Any]


class FullRecursiveConfiguration(object):
    name: str
    complex: ComplexConfig
    complex_object: ComplexObjectConfig


class ConfigurationTests(unittest.TestCase):
    def setUp(self):
        # sc = ServiceCollection(globals())
        # sc.configure()
        # sc.singletons([])
        pass

    def test_that_configure_can_take_a_dict_value(self):
        sc = ServiceCollection.instance(globals())
        sc.configure(ConfigureClass, {
            'name': 'hello',
        })
        sp = sc.build_service_provider()
        conf = sp.get_service(ConfigureClass)
        self.assertEqual(conf.name, "hello")

    def test_that_a_bad_configuration_class_throws_an_exception(self):
        sc = ServiceCollection.instance(globals())
        sc.configure(ConfigureClass2, {
            'name': 'hello'
        })
        sp = sc.build_service_provider()
        with self.assertRaises(
            RuntimeError,
            msg=("There are no known mapped properties of your configuration class.  " +
                 "You need to globally specify the property.  Please consult documentation.")):
            sp.get_service(ConfigureClass2)

    def test_can_recursively_create_a_complex_configuration_object(self):
        """ deep check for completely transformed nested objects """
        sc = ServiceCollection.instance(globals())
        ctxt = ConfigurationContext("tests/settings.json")
        sc.configure(FullRecursiveConfiguration, ctxt)
        sp = sc.build_service_provider()
        fc = sp.get_service(FullRecursiveConfiguration)

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

        sc = ServiceCollection.instance(globals())
        ctxt = ConfigurationContext("tests/settings.json", "target1")
        sc.configure(FullRecursiveConfiguration, ctxt)
        sp = sc.build_service_provider()
        fc = sp.get_service(FullRecursiveConfiguration)

        self.assertEqual(fc.name, "hello")
        self.assertEqual(fc.complex.name, "hello2")
        self.assertEqual(fc.complex_object.complex1.term1, "one")
        self.assertEqual(fc.complex_object.complex1.term2, "two")
        self.assertEqual(fc.complex_object.value1, False)
        self.assertEqual(fc.complex_object.value2, 1)
        self.assertListEqual(fc.complex_object.value3, [6, 7, 8, 9, 10])

    def test_can_recusrively_create_a_complex_configuration_object_with_context_object(self):
        sc = ServiceCollection.instance(globals())
        ctxt = ConfigurationContext("tests/settings.json")
        sc.configure(FullRecursiveConfiguration, ctxt)
        sp = sc.build_service_provider()
        fc = sp.get_service(FullRecursiveConfiguration)

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

    def test_can_use_sections_populate_configuration_objects(self):
        sc = ServiceCollection.instance(globals())
        ctxt = ConfigurationContext("tests/settings.json")
        sc.configure(ComplexOneConfig, ctxt.get_section("complex_object:complex1"))
        sp = sc.build_service_provider()
        conf = sp.get_service(ComplexOneConfig)
        self.assertEqual(conf.term1, "one")
        self.assertEqual(conf.term2, "two")

    def test_can_use_custom_contexts_to_map_configuration_objects(self):
        class CustomConfigurationContext(ConfigurationContext):
            def __init__(self, file: str, target: Optional[str] = None, override_evn_name: Optional[str] = None):
                super().__init__(file, target, override_evn_name)

            @property
            def complex_one_conf(self):
                return self.get_section("complex_object:complex1")

        sc = ServiceCollection.instance(globals())
        ctxt = CustomConfigurationContext("tests/settings.json")
        sc.configure(ComplexOneConfig, ctxt.complex_one_conf)
        sp = sc.build_service_provider()
        conf = sp.get_service(ComplexOneConfig)
        self.assertEqual(conf.term1, "one")
        self.assertEqual(conf.term2, "two")
