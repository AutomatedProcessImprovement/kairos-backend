from kairos.factory import create_app

app = create_app()
app.config.from_object('config.Config')