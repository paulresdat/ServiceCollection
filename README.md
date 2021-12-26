# Service Collection Factory for Python CLI Apps

A simple python module that automates service dependencies using Python's new type hints.  This approach is inspired by automatic dependency resolution in statically typed languages.  This fancy factory pattern also encourages a stricter dependency resolution by only allowing automatic resolution through the approach of injecting the service through a class's constructor.


## Intended Audience

This package's primary audience is the creator for his own projects but if you know a little about dependency injection and clean architecture, this approach should be easy to understand.  If you're a Python beginner, this approach should be coupled with some reading on clean architecture and dependency injection.  It is expected that you will eventually pick up a book on the of topic software architecture.  If you're coming from a C# background, this should be rather strikingly similar to you and you should be able to start working with it immediately regardless of your Python experience.  This library's intended use is for larger maintainable python applications or cron jobs that potentially more than one person would touch.


## Features

* Written with the express intent for ease of unit/integration testing
* Supports json settings files
* Supports settings transformations for multi-target deployment
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

## Examples