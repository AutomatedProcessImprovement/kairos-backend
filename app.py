from kairos.factory import create_app

app = create_app()
app.config.from_object('config.Config')

# app.run() # only for development (will run app on :5000, which interferes with docker container)
