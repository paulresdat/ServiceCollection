import unittest
from src.service_collection.servicecollection import ServiceCollection, ServiceProvider

class B(object):
    def __init__(self):
        self.__name = "n/a"
        pass

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, val: str):
        self.__name = val


class A(object):
    def __init__(self, b: B):
        self._b = b

    def set_name(self, name: str):
        self._b.name = name

    def get_name(self):
        return self._b.name


class TransientB(B):
    def __init__(self):
        super().__init__()


class TransientA(A):
    def __init__(self, b: TransientB):
        super().__init__(b)


class TestServiceCollection(unittest.TestCase):

    def setUp(self):
        sc = ServiceCollection(globals())
        sc.singletons([A, B])
        sc.transients([TransientA, TransientB])
        sp: ServiceProvider = sc.build_service_provider()
        self.sp = sp
        

    def test_that_singletons_are_available_in_the_service_provider(self):
        a: A = self.sp.get_service(A)
        self.assertEqual(a.get_name(), "n/a")
        a.set_name("hi")
        self.assertEqual(a.get_name(), "hi")
        
        # demonstrates the singleton property
        # here, B is a dependency and a singleton
        # so when asked for, it should be the
        # same property in A's dependency
        b: B = self.sp.get_service(B)
        self.assertEqual(b.name, "hi")

        # if we change it here then it should also be
        # reflected in A
        b.name = "hello"
        self.assertTrue(a.get_name(), "hello")

    def test_that_transients_are_available_in_the_service_provider(self):
        a: TransientA = self.sp.get_service(TransientA)
        self.assertEqual(a.get_name(), "n/a")
        a.set_name("hi")
        self.assertEqual(a.get_name(), "hi")
        again: TransientA = self.sp.get_service(TransientA)
        self.assertEqual(again.get_name(), "n/a")
