from flask import Flask
from flask.json import JSONEncoder
from flask_cors import CORS

from logging.config import dictConfig

from bson import json_util, ObjectId
from datetime import datetime

from kairos.api.cases_api import cases_api
from kairos.api.event_logs_api import event_logs_api

# configure logging to reduce level to debug
dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "default",
            }
        },
        "root": {"level": "DEBUG", "handlers": ["console"]},
    }
)

# format datetime objects and objectIds from mongoDB
class MongoJsonEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%dT%H:%M:%S")
        if isinstance(obj, ObjectId):
            return str(obj)
        return json_util.default(obj, json_util.CANONICAL_JSON_OPTIONS)

# create app and register blueprints
def create_app():
    app = Flask(__name__)
    CORS(app)
    app.json_encoder = MongoJsonEncoder
    app.register_blueprint(cases_api)
    app.register_blueprint(event_logs_api)
    
    return app
