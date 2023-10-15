from flaskAppFactory import flaskApp
import asyncio

async def main():

    app = await flaskApp.create_app()
    
    app.run(host='0.0.0.0')

if __name__ == '__main__':
    asyncio.run(main())
