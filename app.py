from kairos.factory import create_app

if __name__ == "__main__":
    app = create_app()
    app.config.from_pyfile('config.py')

    app.run()
