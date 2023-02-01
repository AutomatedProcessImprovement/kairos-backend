from flask import Flask, Response, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
import json
from flask_caching import Cache
import datetime
import pandas as pd
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app, resources={r'/*': {'origins': '*'}})
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['CACHE_TYPE'] = 'SimpleCache'

cache = Cache(app)

client = MongoClient('localhost', 27017)
db = client.flask_db
files = db.files
cases = db.cases
kpi = None

ALLOWED_EXTENSIONS = ['csv', 'xes']
PATH_TO_LOGS = './logs/'

def initial():
    global kpi
    with open('data.json') as f:
        data = json.load(f)
        kpi = data['kpi']
        for case in data['cases']:
            case["status"] = "Completed" if [obj for obj in case["activities"] if obj["name"] == "End Event"] else "Open"
            try:
                cases.insert_one(case)
            except:
                print(f'Case {case["_id"]} already exists')
                continue

def save_file(file):
    filename = secure_filename(file.filename)
    path_to_file = str(datetime.datetime.now().timestamp() * 1000) + "_" + filename
    file.save(os.path.join(PATH_TO_LOGS, path_to_file))
    return path_to_file

initial()

@app.route('/')
def index():
    return "hello world"

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return Response('No file found',400)
    file = request.files['file']
    if not file and not allowed_file(file.filename):
        return Response('Incorrect file extension',400)
    path_to_file = save_file(file)
    file_id = files.insert_one({'path': path_to_file,'delimiter': request.form.get('delimiter'), 'datetime': datetime.datetime.now()}).inserted_id
    return jsonify(fileId = str(file_id))

@app.route('/parse/<file_id>', methods=['PUT'])
def parse_file(file_id):
    try:
        file = files.find_one({"_id": ObjectId(file_id)})
        df = pd.read_csv(PATH_TO_LOGS + file['path'], sep=file['delimiter'])
        header = list(df.columns)
        rows = df.values[:7].tolist()
        return jsonify(header = header, rows = rows)
    except:
        return Response(f"File with id {file_id} not found",404)

@app.route('/update/<file_id>', methods=['POST'])
def update_types(file_id):
    types = request.form.get('types')
    try:
        files.find_one_and_update({"_id": ObjectId(file_id)},{"$set":{"types": types}})
    except:
        return Response(f'File with {file_id} not found',404)
    # TODO send file and types to zhaosi
    return Response('Types updated successfully',200)

@app.route('/parameters/<file_id>', methods=['POST'])
def parameters(file_id):
    positive_outcome = request.form.get('positive_outcome')
    treatment = request.form.get('treatment')
    try:
        files.find_one_and_update({"_id": ObjectId(file_id)},
                                    {"$set":{
                                        "positiveOutcome": positive_outcome,
                                        "treatment": treatment}})
    except:
        return Response(f"File with id {file_id} not found",404)

    # TODO send parameters to zhaosi
    return Response('Parameters saved successfully',200)

@app.route('/eventlogs')
def get_eventlogs():
    fs = files.find({})
    # [print(l) for l in f]
    logs = [{"_id": str(log["_id"]),'filename': log["path"].split('_',1)[1], 'uploadDate': log['datetime']} for log in fs]
    # print(list(fs))
    return jsonify(eventlogs = logs)

@app.route('/eventlogs/<file_id>')
def get_eventlog(file_id):
    log = files.find_one({"_id": ObjectId(file_id)})
    e = {"_id": str(log['_id']),'filename': log["path"].split('_',1)[1],'uploadDate' : log['datetime']}
    return jsonify(eventlog = e)

@app.route('/cases')
def get_cases():
    global kpi
    c = cases.find({})
    return jsonify(kpi = kpi, cases = list(c))

@app.route('/cases/<case_id>')
# @cache.cached(timeout=50)
def get_case(case_id):
    global kpi
    c = [obj for obj in list(cases.find({})) if str(obj["_id"]) == str(case_id)][0]
    return jsonify(kpi = kpi, case = c)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

