from flask import Flask, Response, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
import gridfs
import csv
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
        file_id = fs.put(file)
        print(file_id)
        res = jsonify(fileId = str(file_id))
        return res
    return Response('Incorrect file extension',400)

@app.route('/parse/<file_id>', methods=['POST'])
def parse_file(file_id):
    print(file_id)
    delimiter = request.form.get('delimiter')
    file = fs.find({'_id': ObjectId(file_id)})
    print(file)
    if not file:
        return Response(f"File with id {file_id} not found",404)
    rows = []
    data = file.read()
    for i in range(10):
        print(file.readline())
    csv_reader = csv.reader(data, delimiter)
    header = next(csv_reader)
    ind = 0
    for row in csv_reader:
        rows.append(row)
        ind += 1
        if ind == 10:
            break
    return Response({'header': header, 'rows': rows},200)

@app.route('/update/<file_id>', methods=['POST'])
def update_types(file_id):
    file = fs.find({'_id': ObjectId(file_id)})
    if not file:
        return Response(f"File with id {file_id} not found",404)
    types = request.form.get('types')
    date_format = request.form.get('dateFormat')
    # TODO send file to zhaosi
    return Response('Types updated successfully',200)

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

