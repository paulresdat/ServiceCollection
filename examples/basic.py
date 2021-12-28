from __future__ import annotations
import asyncio
import random
from asyncio.tasks import Task
from typing import Any, List
from servicecollection import ServiceCollection


# A little program that basically spins off threads with random wait times.
# This demonstrates a basic service collection use case within the context
# of a multithreaded application.  The service collection is agnostic to how
# you write your program, as long as the resolution of the service happens
# in the parent thread.
class Spawner(object):
    def __init__(self):
        pass

    async def go(self, name: str):
        rand = random.randint(0, 4)
        print("Starting thread " + name + " - sleeping : " + str(rand))
        await asyncio.sleep(rand)
        print("Ending thread: " + name)


class MassiveSpawner(object):
    def __init__(self, spawner: Spawner, config: SpawnConfig):
        self.__spawner = spawner
        self.__config = config
        self.__spawn_name = "number_"

    async def spawn(self):
        tasks: List[Task[Any]] = []
        for i in range(0, self.__config.spawn_amount):
            task = asyncio.create_task(self.__spawner.go(self.__spawn_name + " " + str(i + 1)))
            tasks.append(task)
        await asyncio.wait(tasks)


class SpawnConfig(object):
    spawn_amount: int = 0


async def main():
    sc = ServiceCollection.instance(globals())
    sc.configure(SpawnConfig, {
        'spawn_amount': 40,
    })
    sc.singletons([Spawner, MassiveSpawner])
    sp = sc.build_service_provider()
    ms = sp.get_service(MassiveSpawner)
    # asynchronously spawns threads that print and sleep a random number of seconds
    await ms.spawn()

if __name__ == '__main__':
    asyncio.run(main())
