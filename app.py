from flask import Flask, Response, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
import gridfs
import string
import json
from flask_caching import Cache


app = Flask(__name__)
CORS(app, resources={r'/*': {'origins': '*'}})
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['CACHE_TYPE'] = 'SimpleCache'

cache = Cache(app)

client = MongoClient('localhost', 27017)
db = client.flask_db
fs = gridfs.GridFS(db)
cases = db.cases
kpi = None

ALLOWED_EXTENSIONS = ['csv', 'xes']

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

initial()

@app.route('/')
def index():
    return "hello world"

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return Response('No file found',400)
    file = request.files['file']
    if file and allowed_file(file.filename):
        file_id = fs.put(file, delimiter = request.form.get('delimiter'), filename = file.filename)
        return jsonify(fileId = str(file_id))
    return Response('Incorrect file extension',400)

@app.route('/parse/<file_id>', methods=['PUT'])
def parse_file(file_id):
    file = fs.get(ObjectId(file_id))
    delimiter = file.delimiter
    if not file:
        return Response(f"File with id {file_id} not found",404)
    rows = []
    header = []
    for i in range(7):
        if i == 0:
            header = str(file.readline().strip()).translate(str.maketrans('','','\"\''))
            header = header[1:]
            header = header.split(delimiter)
        else:
            row = str(file.readline().strip()).translate(str.maketrans('','','\"\''))
            row = row[1:]
            row = row.split(delimiter)
            rows.append([row])
    return jsonify(header = header, rows = list(rows))

@app.route('/update/<file_id>', methods=['POST'])
def update_types(file_id):
    file = fs.get(ObjectId(file_id))
    if not file:
        return Response(f"File with id {file_id} not found",404)
    types = request.form.get('types')
    date_format = request.form.get('dateFormat')
    # TODO send file to zhaosi
    return Response('Types updated successfully',200)

@app.route('/eventlogs')
def get_eventlogs():
    files = fs.find({})
    logs = [{"_id": str(log._id),'filename': log.filename,'uploadDate' : log.uploadDate} for log in files]
    return jsonify(eventlogs = logs)

@app.route('/eventlogs/<file_id>')
def get_eventlog(file_id):
    log = fs.get(ObjectId(file_id))
    e = {"_id": str(log._id),'filename': log.filename,'uploadDate' : log.uploadDate}
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

@app.route('/parameters/<file_id>', methods=['POST'])
def parameters(file_id):
    file = fs.get(ObjectId(file_id))
    if not file:
        return Response(f"File with id {file_id} not found",404)
    positive_outcome = request.form.get('positive_outcome')
    treatment = request.form.get('treatment')
    # TODO send parameters to zhaosi
    return Response('Parameters saved successfully',200)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

