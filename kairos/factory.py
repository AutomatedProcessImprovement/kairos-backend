from flask import Flask
from flask.json import JSONEncoder
from flask_cors import CORS

from bson import json_util, ObjectId
from datetime import datetime
import os

from kairos.api.cases_api import cases_api
from kairos.api.event_logs_api import event_logs_api


class MongoJsonEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%dT%H:%M:%SZ")
        if isinstance(obj, ObjectId):
            return str(obj)
        return json_util.default(obj, json_util.CANONICAL_JSON_OPTIONS)


def create_app():
    app = Flask(__name__)
    CORS(app)
    app.json_encoder = MongoJsonEncoder
    app.register_blueprint(cases_api)
    app.register_blueprint(event_logs_api)
    app.config["MONGO_URI"] = os.environ.get("MONGO_URI", 'mongodb://mongo:27017/flask_db')
    app.config["PRCORE_HEADERS"] = {'Authorization':'Bearer UaJW0QvkMA1cVnOXB89E0NbLf3JRRoHwv2wWmaY5v=QYpaxr1UD9/FupeZ85sa2r'}
    app.config["PRCORE_BASE_URL"] = 'https://prcore.chaos.run'

    return app
