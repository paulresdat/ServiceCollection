from abc import ABCMeta, abstractmethod

class Foo(metaclass=ABCMeta):
    def __subclasshook__(*args):
        return (hasattr(args[0], 'foo') and callable(args[0].foo))
    @abstractmethod
    def foo(self):
        raise NotImplemented


class Bar(Foo):
    def foo(self):
        print('hi')

print(isinstance(Bar(), Foo))
issubclass(Bar, Foo)