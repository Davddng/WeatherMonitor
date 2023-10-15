import asyncio
import time

async def main(name="default", **kwargs):
    print(name)
    print(kwargs)

if __name__ == "__main__":
    asyncio.run(main(name="testName", var1="testVar1", var2="testVar2"))