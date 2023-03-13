from flask import Flask, Blueprint
from flask.json import JSONEncoder
from flask_cors import CORS

from bson import json_util, ObjectId
from datetime import datetime

from kairos.api.cases_api import cases_api
from kairos.api.event_logs_api import event_logs_api


class MongoJsonEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(obj, ObjectId):
            return str(obj)
        return json_util.default(obj, json_util.CANONICAL_JSON_OPTIONS)


def create_app():
    app = Flask(__name__)
    CORS(app)
    app.json_encoder = MongoJsonEncoder
    api = Blueprint('api', __name__, url_prefix='/api')
    api.register_blueprint(cases_api)
    api.register_blueprint(event_logs_api)
    
    app.register_blueprint(api)

    return app
