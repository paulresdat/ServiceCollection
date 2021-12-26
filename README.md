# Service Collection Factory for Python CLI Apps

A simple python module that automates service dependencies using Python's new type hints.  This approach is inspired by automatic dependency resolution in statically typed languages.

Beta version 0.0.1

```python
sc = ServiceCollection(globals())
sc.singletons([MyFirstClass, MySecondClass])
sp: ServiceProvider = sc.build_service_provider()
myClass: MyFirstClass = sp.get_service(MyFirstClass)

myClass.doSomething()
```

## Intended Audience

This package's primary audience is the creator for his own projects but if you know a little about dependency injection and clean architecture, this approach should be easy to understand.  If you're a Python beginner, this approach should be coupled with some reading on clean architecture and dependency injection.  It is expected that you will eventually pick up a book on the of topic software architecture.  If you're coming from a C# background, this should be rather strikingly similar to you and you should be able to start working with it immediately regardless of your Python experience.  This library's intended use is for larger maintainable python applications or cron jobs that potentially more than one person would touch.


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

Automatic service injection by reflection in statically typed languages have been around for a while.  Python however is a duck typed language where variables can be of any type.  Later versions of Python introduced type hinting and annotations that allow us to now inspect objects to get at a type hint on a variable or argument.  This is similar in respect to reflection in statically typed languages like C#.  Now that we can view this data by type and not by instantiation, we can resolve dependencies with explicit type hinting without expecting an already instantiated object.  This opens up the door for automating dependency injection without a long list of boiler plate code to adhere to the design.


### Singletons, Transients and Configurations

There are 3 main resolution types to be aware of, singletons, transients and configuration objects.

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
        self.__property_one: str = None

    @property
    def property_one(self):
        return self.__property_one

    @property_one.setter
    def property_one(self, val: str):
        self.__property_one = val
```


## Anatomy of an App

The fancy factory pattern of automatic resolution of dependencies in this library encourages a stricter dependency resolution by allowing automatic resolution only through the approach of injecting the service through a class's constructor.  In this beta version, there are no plans to use injection in any other fashion and there currently is no need to use any wrapper functions to help in the resolution of dependencies.  Let us go forth with examples to illustrate how to approach a new application with this library.  Please note some implementation details of objects may be omitted because the following is only used as illustrations of the concept.  In "Examples", you will find working code in practice.

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
from utitlities import CsvMaker, SqlConnection, SqlConfig

# Using TYPE_CHECKING variable is very important in case you have a lot of dependencies.
# Importing them everywhere in objects that only use the type hints can cause circular
# reference problems in Python's import resolution logic.  It's important to make use
# of this when a file only uses type hints of the object.
if TYPE_CHECKING:
    # We need this for type hinting and do not need to import it 
    # directly, so only import for type checking resolution.
    from servicecollection import ServiceProvider

def main():
    # we must define the service collection and pass all defined imports and
    # variables from the `globals()` of this document.
    # You can read for more details on using `globals()` later in this document.
    sc = ServiceCollection(globals())
    # configure your config object that SqlConnection relies on
    sc.configure(SqlConfig, {
        'username': 'user1',
        'password': 'password123',
        'database': 'sysdb',
    })
    # register your singletons
    sc.singletons([CsvMaker, SqlConnection])
    # build the service provider
    sp: ServiceProvider = sc.build_service_provider()
    # get your main service, your single entry point
    csv: CsvMaker = sp.get_service(CsvMaker)
    # run the job
    csv.get_daily_totals("daily-totals.csv")
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

The important thing to note here, is that the `SqlConnection` object is a dependency in the constructor of `CsvMaker` and that it's type hint is explicitly stated in the constructor.  This is how the service collection library knows about the `SqlConnection` class as a dependency in `CsvMaker`.  The service collection library can automatically resolve this because it knows what that type is in the constructor of that class.  In fact, as long as the type is registered in the service collection, you can push that type into any class constructor you wish that is also registered in the service collection.  This makes dependency injection very easy in this library.

Let us now inspect the `SqlConnection` object:

```python
# in utilities.py

class SqlConnection(object):
    # here we are saying that the SqlConfig object is a dependency in the constructor of the SqlConnection object
    def __init__(self, sql_config: SqlConfig):
        self.__sql_config = sql_config
        self.__connection = self.__connect({
            'username': sql_config.username
            'password': sql_config.password
            ...
        })

    def get_totals(self) -> List[List[Any]]:
        self.__connection.fetch("select * from Totals")
        ...
```

The important thing to note here is the same principle is applied from the CsvMaker where the configuration object is a dependency in the constructor so that the service injection library can automatically resolve that for you.

## Examples

## Important Notes

### Globals

### Type Hinting Resolution