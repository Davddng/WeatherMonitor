import asyncio
import time

async def cancel_me():
    print('inside')
    await asyncio.sleep(10)
    print('done sleep')

def createTask():
    return asyncio.create_task(cancel_me())

async def main():
    # Create a "cancel_me" Task
    loop = createTask()

    await loop

if __name__ == "__main__":
    asyncio.run(main())