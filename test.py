import asyncio
async def set_after(fut, delay, value):
    # Sleep for *delay* seconds.
    print('inside!')

    await asyncio.sleep(delay)
    print('hello ...')

    # Set *value* as a result of *fut* Future.
    fut.set_result(value)

async def main():
    # Get the current event loop.
    loop = asyncio.get_running_loop()

    # Create a new Future object.
    fut = loop.create_future()

    # Run "set_after()" coroutine in a parallel Task.
    # We are using the low-level "loop.create_task()" API here because
    # we already have a reference to the event loop at hand.
    # Otherwise we could have just used "asyncio.create_task()".
    print("start")
    loop.create_task(
        set_after(fut, 5, '... world'))

    await asyncio.sleep(5)
    print('hello ...')

    # Wait until *fut* has a result (1 second) and print it.
    print(await fut)

asyncio.run(main())