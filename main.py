from flaskAppFactory import createFlaskApp

def main():

    app = createFlaskApp()
    
    app.run(host='0.0.0.0')

if __name__ == '__main__':
    main()