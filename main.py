from flaskAppFactory import create_app

async def main():

    app = await create_app()
    
    app.run(host='0.0.0.0')

if __name__ == '__main__':
    main()
