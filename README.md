# Service Collection Factory for Python CLI Apps

A simple python module that automates service dependencies using Python's new type hints.  This approach is inspired by automatic dependency resolution in statically typed languages.

Beta version 0.0.1

```python
sc = ServiceCollection.instance(globals())
sc.singleton(IMyClass, MyClass)
sp = sc.build_service_provider()
myClass = sp.get_service(IMyClass)

myClass.doSomething()
```

## Intended Audience

This package's primary audience is the creator for his own projects but if you know a little about dependency injection and clean architecture, this approach should be easy to understand.  If you're a Python beginner, this approach should be coupled with some reading on clean architecture and dependency injection.  It is expected that you will eventually pick up a book on the topic of software architecture.  If you're coming from a C# background, this should be strikingly familiar to you and you should be able to start working with it immediately regardless of your Python experience.  This library's intended use is for larger maintainable python applications or a project with a team where there are collaborators.


## Features

* Written with the express intent for ease of unit/integration testing
* Supports injecting settings using JSON files
* Supports transformations for multi-target deployment
* Fully automates injecting dependencies based on types
* Written with the express intent to encourage clean architecture principles


## Installing

```bash
pip install servicecollection
```

## Documentation

### Primer

Automatic service injection by reflection in statically typed languages have been around for a while.  Python however is a duck typed language where variables can be of any type.  Later versions of Python introduced type hinting and annotations that allow us to now inspect objects to get at a type hint on a variable or argument.  This is similar in respect to reflection in statically typed languages like C#.  Now that we can view this data by type and not by instantiation, we can resolve dependencies with explicit type hinting without expecting an already instantiated object.  This opens up the door for automating dependency injection without a long list of boiler plate code to adhere to the design.

This way of using dependencies with a single point of entry allows the programmer to focus almost entirely on the act of programming the application, how these classes interact with each other, and the architecture of the software itself without dealing with the boiler plate code that comes with manual dependency injection.  Classes are the primary vehicle used within the service collection which coerces the application to work within a class dominated software architecture.  So class types are the expected object as dependencies that are only injected through the constructor or `__init__` method of a class.  There will never be any other way of doing it in this library.

This approach may not be for everyone, since Python is a very fluid language, folks find themselves in comfort zones because they know their own code.  I like to write almost entirely in classes and I like the SOLID principle approach to software architecture and I appreciate a good dependency injection paradigm, and if I can automate injection by class types, I'm gonna do it.  Type hints allows me to do this.  This library is for me mostly but if you like it, I'm open to suggestions and contributions.


### Singletons, Transients and Configurations

There are 3 main resolution types to be aware of: singletons, transients and configuration objects.

```python
sc = ServiceCollection.instance(globals())
sc.singleton(SingletonClass)
sc.transient(TransientClass)
sc.configure(ConfigurationClass, {})
```

#### Singletons

<a href="https://en.wikipedia.org/wiki/Singleton_pattern">Singletons are a design pattern</a>, where only one instance of an object can exist in memory for that type.  The service collection resolves the type asked for at run time and returns the same instance if it was already created or a new instance if it was not.  It keeps the instance in memory and always returns that same instance throughout the life of the application.  In essence, only one instance of that object can be created at a time.

This pattern is very useful for high level objects like services and repositories.  If we had a repository design object that had a long running connection to a third party application, it would make sense to have one instance of that object in memory and return the same object to any service requesting it.  This allows for the application to share the same connection across its business logic classes.

#### Transients

Transients are objects that are instantiated upon resolution, so many instances of the object can exist in the lifetime of the app.  It is the opposite of the singleton design.  Every time it is asked for as a dependency a new object is created and provided.

#### Configurations

The configuration objects are transients in practice but are handled in a special way.  These objects in other service injection software are called "Options" or "Settings".  Basically, we can map static data to explicit objects.  This moves out of the realm of passing dictionary objects everywhere and pushes us more into the realm of passing explicitly defined objects everywhere.  A configuration object may look like this:

```python
class ConfigObject(object):
    property_one: str
    property_two: int
    property_three: bool
```

And it is possible to use getter and setter properties for configuration objects, however you MUST still define the property outside the `__init__` method.  This tells the service collection what to map to explicitly and is a requirement whether you have getters/setters and private fields or not to define those properties internally.

```python
class ConfigObject(object):
    property_one: str
    def __init__(self):
        self.__property_one: Optional[str] = None

    @property
    def property_one(self):
        return self.__property_one

    @property_one.setter
    def property_one(self, val: str):
        self.__property_one = val
```


## Anatomy of an App

This fancy factory pattern of automatic resolution of dependencies encourages a stricter dependency resolution by allowing automatic resolution only through the approach of injecting the service through a class's constructor.  In this beta version, there are no plans to use injection in any other fashion and there currently is no need to use any wrapper functions to help in the resolution of dependencies.  This forces us to think about an app almost entirely as a collection of classes in modules rather than a collection of methods and or classes in a monolithic file.  Let us go forth with examples to illustrate how to approach a new application with this library.  Please note some implementation details of objects may be omitted because the following is only used as illustrations of the concept.  In "Examples", you will find working code in practice.

### Basic Structure

A basic folder structure could be something like the following:

```bash
app/
  - main.py
  - lib/
    - utilities.py
```

Where the main entry point of your application is `main.py` and the logic for your app is found within the lib/ folder under utilities.  This is very simple but primarily, when working in this paradigm of dependency injection, we must explicitly define our entry point where all our dependencies are defined.  This would happen in `main.py` and it could look something like this:

```python
from __future__ import annotations
from typing import TYPE_CHECKING
from servicecollection import ServiceCollection
from lib.utitlities import CsvMaker, SqlConnection, SqlConfig


def main():
    # We must define the service collection and pass the global symbol table.
    # ServiceCollection is a factory static class that returns a IServiceCollection
    # interface where the implementation details reside behind a concealed class.
    sc = ServiceCollection.instance(globals())
    # configure your config object that SqlConnection relies on
    sc.configure(SqlConfig, {
        'username': 'user1',
        'password': 'password123',
        'database': 'sysdb',
    })
    # register your singletons, in this case they do not have interfaces
    sc.singletons([CsvMaker, SqlConnection])
    # build the service provider, returns the IServiceProvider interface
    sp = sc.build_service_provider()
    # get your main service, your single entry point
    csv = sp.get_service(CsvMaker)
    # run the job
    csv.get_daily_totals("daily-totals.csv")


if __name__ == '__main__':
    main()
```

From this example we can infer a few things.  We see 3 classes: `CsvMaker`, `SqlConnection`, and `SqlConfig`.  We can see that there is only one place of entry: `CsvMaker`.  We can also infer that the `SqlConnection` object may be a dependency of `CsvMaker`.  `SqlConfig` object we don't know for sure from just this example where that object is being used, but we can infer from the variable name that it's likely used in the `SqlConnection` object.  So we have a rough idea of what's going on, let us look at what the CsvMaker might entail:

```python
# in utitlies.py

class CsvMaker(object):
    # here the type `SqlConnection` MUST be specified with the type hint so that
    # the service collection knows `SqlConnection` should be injected.
    def __init__(self, sql_conn: SqlConnection):
        self.__sql_conn = sql_conn

    def get_daily_totals(self, save_file_name: str):
        filename = save_file_name
        totals = self.__sql_conn.get_totals()
        self.__save_file(filename, totals)
```

The important thing to note here is that the `SqlConnection` object is a dependency in the constructor of `CsvMaker` and that its type hint is explicitly stated in the constructor.  This is how the service collection library knows about the `SqlConnection` class as a dependency in `CsvMaker`.  The service collection library can automatically resolve this because it knows what that type is in the constructor of that class.  In fact, as long as the type is registered in the service collection, you can push that type into any class constructor you wish that is also registered in the service collection.  This makes dependency injection very easy in this library.

Let us now inspect the `SqlConfig` configuration object and the `SqlConnection` service object:

```python
# in utilities.py
class SqlConfig(object):
    username: str
    password: str
    database: str


class SqlConnection(object):
    # here we are saying that the SqlConfig object is a dependency in the constructor of the SqlConnection object
    def __init__(self, sql_config: SqlConfig):
        self.__sql_config = sql_config
        self.__connection = self.__connect({
            'username': sql_config.username,
            'password': sql_config.password,
            ...
        })

    def get_totals(self) -> List[List[Any]]:
        self.__connection.fetch("select * from Totals")
        ...
```

The important thing to note here is the same principle is applied from the CsvMaker where the configuration object is a dependency in the constructor so that the service injection library can automatically resolve that for you. Here we see an example that the values that are specified in `main.py` is what is registered with the `SqlConfig` object.  This is an example of centrally defining settings in one place that's then used throughout the application where it is asked for.  Using settings JSON files is described in more details below.

We can see from the above example how the architecture of an app can look, and we've demonstrated some simple injection principles as well as a basic configuration class.  This approach can differ from how folks usually write Python applications.  Even though dependency injection and service resolution does exist in Python, one can tell they're applied in a different kind of way for already existing applications that may not previously had automatic dependency resolution.  This library encourages us to look at the entire architecture and design of your app from the ground up at the start of tackling a new project.

### Configurations and Settings

In this section we will be discussing the different scanarios you may need to setup static configuration data that you may need to pass around in your application.  There are 3 main ways of doing it, one way being an explicit approach for testing.  However there is a recommended way of using static data for your application, and that's by using JSON files that are then transformed to objects in memory when the application starts.  Below are the examples of 3 main ways you use configurations.

#### Configurations and Dictionaries

```python
class ConfigObject(object):
    property_one: str
    property_two: str

sc.configure(ConfigObject, {
    'property_one': 'one',
    'property_two': 'two',
})
```

This is the simplest example of the use of configurations: a direct dictionary is given and is mapped to the type on service resolution.  This is particularly handy when testing your app with values you need specifically in a testing environment.  It's also for a shortcut in a small app where you may not need JSON transformation files for targeting multiple environments.


#### Configurations and Argparse

```python
import argparse

class ConfigObject(object):
    property_one: str
    property_two: bool

parser = argparse.ArgumentParser(description='Argument parsing for configuration tests')
parser.add_argument('--property-one', type=str, help='Property one as a string')
parser.add_argument('--property-two', type=bool, action='store_true', help='Property two as a boolean value')
args = parser.parse_args(sys_args if sys_args else ['--help'])

sc = ServiceCollection.instance(globals())
sc.configure(ConfigObject, args)
```

Argparse is a great library offered to you out of the box with python.  It automates command line argument parsing with some nice value adds like automatic boolean assignment and default values.  This library endeavours for first class support in mapping argparse to configuration objects.  The argparse.Namespace lacks in intellisense and lookup of your variable names.  Using configuration objects can be more readable in the long run and allows for us to utilize our IDE's intellisense for variable resolution and auto typing.  For more information on Argparse, you can consult the Python documentation.


#### Configurations and JSON files

*Example 1:*

> settings.json
```json
{
    "property_one": "one",
    "property_two": true
}
```

> main.py
```python

class ConfigObject(object):
    property_one: str
    property_two: bool

sc = ServiceCollection.instance(globals())
ctxt = ConfigurationContext("settings.json")
sc.configure(ConfigObject, ctxt)
```

This is the simplest example where we simply provide the entire context to the configure method.  This basically maps the entire file to that one object.


*Example 2:*

> settings.json
```json
{
    "sql_configurations": {
        "db_connections": {
            "username": "sa",
            "password": "Password123",
            "database": "sysdb"
        },
        "sql_log": {
            "property_one": "one"
        }
    },
    "chat_configurations": {
        "long_running": true
    }
}
```

> main.py
```python
class DbConnectionConfig(object):
    username: str
    password: str
    database: str

class SqlLogConfig(object):
    property_one: str

class ChatConfig(object):
    long_running: bool

sc = ServiceCollection.instance(globals())
ctxt = ConfigurationContext("settings.json")
sc.configure(DbConnectionConfig, ctxt.section("sql_configurations:db_connections"))
sc.configure(SqlLogConfig, ctxt.section("sql_configurations:sql_log"))
sc.configure(ChatConfig, ctxt.section("chat_configurations"))
```

This example illustrates the ability to section off a settings file into different areas of concern.  This allows us to slice up the settings into different configuration objecst that are used in different areas of the application.  This helps enforce separation of concern in our configurations.


*Example 3 (custom context object, the most explicit):*

> settings.json
```json
{
    "sql_configurations": {
        "db_connections": {
            "username": "sa",
            "password": "Password123",
            "database": "sysdb"
        },
        "sql_log": {
            "property_one": "one"
        }
    },
    "chat_configurations": {
        "long_running": true,
        "amqp_conn": {
            "username": "sa",
            "password": "Password123",
            "queue": "queue-a",
            "ip": "127.0.0.1",
            "port": 5672
        }
    }
}
```

> main.py
```python
class DbConnectionConfig(object):
    username: str
    password: str
    database: str

class SqlLogConfig(object):
    property_one: str

class AmqpConnConfig(object):
    username: str
    password: str
    queue: str
    ip: str
    port: int

class ChatConfig(object):
    long_running: bool
    # embedded complex objects are supported and are automatically mapped
    amqp_conn: AmqpConnConfig

class CustomConfigurationContext(ConfigurationContext):
    def __init__(self, filename: str, target: Optional[str] = None, overridden_env_name: Optional[str] = None, json_loader: IJsonLoader = None):
        super().__init__(filename, target, overridden_env_name, json_loader)

    @property
    def db_configurations(self) -> ConfigurationSection:
        return self.section("sql_configurations:db_connections")

    @property
    def sql_log_configurations(self) -> ConfigurationSection:
        return self.section("sql_configurations:sql_log")

    @property
    def chat_configurations(self) -> ConfigurationSection:
        return self.section("chat_configurations")


sc = ServiceCollection.instance(globals())
ctxt = CustomConfigurationContext("settings.json")
sc.configure(DbConnectionConfig, ctxt.db_configurations)
sc.configure(SqlLogConfig, ctxt.sql_log_configurations)
sc.configure(ChatConfig, ctxt.chat_configurations)
```

This exmample illustrates the possibility and recommended way of extending the configuration context class so that configuration sections are exposed to the service collection as properties of the context object itself.  This allows for the best readability of the configuration maping.  For a larger application this example would be the recommended way of bootstrapping your configurations.

#### Custom JSON Loader

Support for a custom JSON loader outside of the standard `json` module allows you to use a different module as long as you wrap it in the `IJsonLoader` interface.  You can then inject that wrapper into the custom configuration object as demonstrated below:

```python
import commentjson

class JsonLoader(IJsonLoader):
    def __init__(self):
        super().__init__();

    def loads(self, data: str):
        return commentjson.loads(data)
 
    def dumps(self, data: Any):
        return commentjson.dumps(data)

ctxt = ConfigurationContext("config.json", json_loader=JsonLoader())
```

I would want to use this instead if I wanted to allow comments.  Comment json is python module you can use instead that allows you to comment out the json file:

```json
{
    // I want to comment in this
    "property_one": 1,
    // And I want to comment out this property
    //"propety_two": 2,
}
```

This works better if you have a config file that requires some fluidity in change.  One example is that I need to download files from multiple servers however most of the time it's from only one.  Sometimes I need to download from the other and I haven't a desire to put both in the configuration file so I just comment out one to place in the other when I need to.  There are probably other reasons but suffice it to say this allows you to use any other JSON module in case the built in `json` module doesn't fit your requirements.

#### Settings Transformations

The 3 main ways of transforming JSON data or dictionaries to configuration objects is outlined above, but what if this app has multiple targets and you have different database connections and third party app configurations that change per target environment.  Welcome settings transformations.  This feature allows you to have setting files in your repository for each target platform as well as dynamically transform them on runtime.  There are 2 main ways to start your transformations.


*Example 1:*
> Specify the target in code
```python
ctxt = ConfigurationContext("settings.json", "target1")
sc.configure(ConfigObject, ctxt)
```

The `target1` setting is saying that the context has a specified target.  It will expect a file called `settings.target1.json` alongside `settings.json` and will first read in `settings.json` and then read in `settings.target1.json` and overwrite any variables.  For example:

> settings.json
```json
{
    "property_one": "one",
    "property_two": {
        "property_three": {
            "term1": "one",
            "term2": "two"
        }
    }
}
```

> settings.target1.json
```json
{
    "property_two": {
        "property_three": {
            "term2": "two"
        }
    }
}
```

The configuration context object will read in `settings.json` and then it will read in `settings.target1.json` and overwrite only the `term2` property in the embedded JSON object.  Be aware that properties will be overwritten entirely:

> settings.target2.json
```json
{
    "property_two": {
        "property_three": null
    }
}
```

This example would overwrite `property_three` to null.  The target settings file always takes precedence.  However, if there are extra properties that are not specified in `settings.json` but specified in the target settings file, it will be merged:

> settings.target3.json
```json
{
    "property_two": {
        "property_three": {
            "term3": "an added term only for target3"
        }
    }
}
```

The resulting transformation from `settings.target3.json` would include `term1`, `term2` and `term3`.


*Example 2:*
> Using an environment variable
```bash
(venv) $> export SERVICE_COLLECTION_ENV="target1"
(venv) $> python main.py
```

The ConfigurationContext object comes aware of the environment variable "SERVICE_COLLECITON_ENV" out of the box.  You can set this variable on your target machine, and it will transform to the target specified by that environment name.  If this environment name does not suffice for you, you can change the environment name in code as such:

```python
ctxt = ConfigurationContext("settings.json", target_context_os_env_name="MY_CUSTOM_ENV_VAR")
```

And in bash:

```bash
(venv) $> export MY_CUSTOM_ENV_VAR="target1"
(venv) $> python main.py
```

The context will now be aware of your own environment variable and will transform to what that environment variable has instead.

#### Quick Note on Context/Configuration Debugging

For ease of use, I've exposed the context as an entire dictionary using Python's inbuilt utilities.  You can access the entire context's dictionary by exploding it as follows: `{ **ctxt }`.  For a configuration section, you can print out it's `settings` attribute which is publically available to you: `ctxt.get_section("setting_one:property").settings`.  Note that the ServiceCollection expects either a context or section object though.  The ability to expose the context as a dictionary is for debugging purposes so you can easily inspect the object by printing out to the console when you're working on your app.


### Using Interfaces/Abstract Classes

Inversion of control employs the Liskov Substitution Principle where if a type T is a subtype of type S, then it can also be of type S.  This means you can subsitute a parent class with a child class in your application and not break it, as long as it adheres to the contract of the parent class.  Python uses abstract classes and a subclass magic method `__subclasshook__` to enforce an interface contract.  We need to use the abstract class library in Python to implement an interface as well asraise errors if the contract from the interface is not met from a child class that implements it.

```python
from abc import ABCMeta, abstractmethod

class IMyClass(metclass=ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass: Any):
        return (
            hasattr(subclass, 'foo') and callable(subclass.foo)
            or NotImplemented
        )

    @abstractmethod
    def foo(self) -> bool:
        raise NotImplementedError


class MyClass(IMyClass):
    def __init__(self):
        pass

    def foo(self):
        return True
```

Now that we've got our contract (the interface IMyClass) and defined an abstract method that must be implmented, we can then use this in our service collection as such:

```python
sc = ServiceCollection.instance(globals())
sc.singleton(IMyClass, MyClass)
sp = sc.build_service_provider()
myClass = sp.get_service(IMyClass)
print(myClass.foo())
```

The following will print "True".  We've successfully decoupled our contract with our implementation in our service collection, and now we can swap out `MyClass` with another class that implements `IMyClass`.

Note that it is possible to chain multiple dependencies using the `singletons` method.  This is a shorthand from writing multiple `singleton` statements:

```python
sc.singletons([
    [IMyClass, MyClass],
    [IMyClass2, MyClass2],
    ... etc ...
])
```

## Unit/Integration Testing

One of the highlights of using dependency injection is that its inversion of dependency paradigm allows us to inject mocked objects that have pre-defined values in a testing context in place of its dependencies.  This decoupling of internal code to injected instances allows us to test our code in a modular fashion.  Coupled code is notoriously more difficult to test.

This library's goal is to have an easy interface for mocking and testing when setting up your dependencies.  The 2 libraries that have been used with the service collection are `pytest` and `unittest`.  Concievably, this library should work with any testing framework.

There's nothing stopping you from setting up your services independently of each other in each method in a testing framework, however the downside is that there is a consierably more verbose boiler plate code in your tests to maintain.  We propose that you use a central service dependency method that registers your services and mocks that your entire file uses.  For instance, if you have a unit tests around the repository, we recommend having them all in the same file and where you may only need one method to return the service provider with the methods registered.  This keeps your code cleaner and less verbose.

```python
# in a unittest file
class TestingRepo(unittest.TestCase):
    # if you just need the service provider without custom mocking for each test
    def setUp(self):
        sc = ServiceCollection.instance(globals())
        sc.addsingletons([ClassA, ClassB])
        self.__sp = sc.build_service_provider()

    def test_when_something_happens(self):
        classA = self.__sp.get_service(ClassA)
        .. do your test ..
```

Or you can create a private method for getting the service provider:

```python
# in a unittest file
class TestingRepo(unittest.TestCase):
    def test_when_something_happens():
        sp = self.__get_sp(True)
        sql_conn = sp.get_service(SqlConnection)
        self.assertTrue(sql_conn.connect())

    def __get_sp(self, mock_sql_conn: False) -> ServiceProvider:
        sc = ServiceCollection.instance(globals())
        # allowing a central point for the service provider while allowing
        # for some conditionals that can change by test
        if mock_sql_conn:
            sql_conn = SqlConnection()
            sql_conn.connect = MagicMock(return_value=True)
            sc.singleton(SqlConnection, lambda: sql_conn)
        else:
            sc.singleton(SqlConnection)

        return sc.build_service_provider()
```

## Examples

Examples can be found in the `examples` folder in this github repository.

## Important Notes

### Adding ServiceCollection to an existing application

You can try and add this library to an existing project.  Depending on the architecture, you may need to slowly migrate over to a new central service provider.  If that's not an option, then you would need to do a rewrite.  With many python scripting apps, slowly migrating may not be an option because the paradigm is very different for implementation using a service provider than how the older app was written.  In such cases it may be the case this library just isn't what's needed for the application in question.  Also, this library is intended for use in later Python versions, this may also be a barrier depending on the target machine that the app resides and whether there are administrative hurtles to update the Python version on the target machine.

Another issue is that this library is intended specifically for command line applications.  There is no support for any of the Python frameworks.  It is completely possible to work with this service provider in the context of a framework, given you know how to wield the framework, but you do run the risk of introducing anti-patterns.


### Avoiding Anti-Patterns

With a service provider, you run the risk of introducing anti-patterns if you try and inject the service provider itself into the architecture of the application.  This is a "single point of origin" service provider that only needs to be instantiated once in the top most layer of the application, call the main entry class (or service) and begin the app.  Moving away from this pattern, you run the risk of breaking the paradigm and injecting anti-patterns.  More information on anti-patterns can be found <a href="https://blog.ploeh.dk/2010/02/03/ServiceLocatorisanAnti-Pattern/">here</a>.

*VERY VERY BAD:*

```python
class ServiceB(object):
    def __init__(self):
        self.__name = "service b"

    @property
    def service_name(self):
        return self.__name

class ServiceA(object):
    def __init__(self, service_provider: ServiceProvider):
        self.__sp = service_provider

    def get_name(self):
        service_b = self.__sp.get_service(ServiceB)
        return service_b.service_name

sc = ServiceCollection.instance(globals)
sc.singletons([ServiceA, ServiceB])
sp sc.build_service_provider()
# BAD, never do this, this is just bad design
sc.singleton(ServiceProvider, lambda: sp)
new_sp = sc.build_service_provider()

s = new_sp.get_service(ServiceA)
# BAD
s.get_name()
```

This an example of bad design.  The service provider is NEVER a dependency in another object.  This should be avoided because it's bad code and bad design.  It's an anti-pattern and will do weird things.  Just avoid that.

*VERY VERY GOOD*

```python
class ServiceB(object):
    def __init__(self):
        self.__name = "service b"

    @property
    def service_name(self):
        return self.__name

class ServiceA(object):
    def __init__(self, service_b: ServiceB):
        self.__service_b = service_provider

    def get_name(self):
        return self.__service_b.service_name

sc = ServiceCollection.instance(globals)
sc.singletons([ServiceA, ServiceB])
sp = sc.build_service_provider()
s = sp.get_service(ServiceA)
s.get_name()
```

The above code of course illustrates what is shown throughout the documentation.  Services are dependencies of each other, and at the top most layer of the application, the service provider is built and then the single point of entry class is fetched and served.


### Globals

It is a requirement to always pass `globals()` when instantiating a new `ServiceCollection` as illustrated from the many examples provided in this document.  `globals()` returns a symbol table that is required for the `ServiceCollection` to correctly resolve dependencies based on their type.

Please note, this is by design.  At this time, there are no plans to change this.  If you feel there's a reason to change it or to update this functionality, please open an issue in the issue tracker to discuss.
