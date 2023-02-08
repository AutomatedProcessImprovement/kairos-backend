from flask import Flask, Response, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
import json
import requests
import datetime

app = Flask(__name__)
CORS(app)

client = MongoClient('localhost', 27017)
db = client.flask_db
files = db.files
cases = db.cases
kpi = None

ALLOWED_EXTENSIONS = ['csv', 'xes']
PATH_TO_LOGS = './logs/'
PRCORE_HEADERS = {'Authorization':'Bearer UaJW0QvkMA1cVnOXB89E0NbLf3JRRoHwv2wWmaY5v=QYpaxr1UD9/FupeZ85sa2r'}
PRCORE_BASE_URL = 'https://prcore.chaos.run'


def initial():
    global kpi
    with open('data.json') as f:
        data = json.load(f)
        kpi = data.get('kpi')
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
        return Response('File not found',400)
    file = request.files['file']
    if not file and not allowed_file(file.filename):
        return Response('Incorrect file extension',400)
    delimiter = request.form.get('delimiter')
    res = requests.post(PRCORE_BASE_URL + '/event_log', files={'file': (file.filename, file.stream, file.content_type), 'separator': delimiter}, headers=PRCORE_HEADERS)
    try:
        res_dict = res.json()
    except:
        print(res)
        return Response('Something went wrong with PrCore',500)
    file_id = files.insert_one({'filename': file.filename, 
                                'event_log_id': res_dict.get('event_log_id'), 
                                'columns_header': res_dict.get('columns_header'), 
                                'columns_definition' : res_dict.get('columns_inferred_definition'),
                                'columns_data': res_dict.get('columns_data'), 
                                'delimiter': delimiter, 
                                'datetime': datetime.datetime.now()}).inserted_id
    return jsonify(fileId = str(file_id))


@app.route('/parse/<file_id>', methods=['GET'])
def parse_file(file_id):
    try:
        file = files.find_one({"_id": ObjectId(file_id)})
        header = file.get('columns_header')
        types = file.get('columns_definition')
        rows = file.get('columns_data')
        return jsonify(header = header, rows = rows, types = types)
    except:
        return Response(f"File with id {file_id} not found",404)

@app.route('/update/<file_id>', methods=['POST'])
def update_types(file_id):
    types = request.get_json()
    try:
        file = files.find_one({"_id": ObjectId(file_id)})
    except:
        return Response(f'File with {file_id} not found',404)
    event_log_id = file.get('event_log_id')
    res = requests.put(PRCORE_BASE_URL + f'/event_log/{event_log_id}', json=types, headers=PRCORE_HEADERS)
    try:
        res_dict = res.json()
    except:
        print(res)
        return Response('Something went wrong with PrCore',500)
    activities = list(res_dict.get('activities_count').keys())
    files.update_one({'_id': file.get('_id')},{"$set": {
                                        "activities": activities,
                                        "columns_definition": types,
                                        "outcome_selections": res_dict['outcome_selections'],
                                        "treatment_selections": res_dict['treatment_selections']}})
    return Response('Types updated successfully',200)

@app.route('/parameters/<file_id>', methods=['POST'])
def parameters(file_id):
    positive_outcome = request.get_json().get('positive_outcome')
    treatment = request.get_json().get('treatment')
    alarm_probability = request.get_json().get('alarm_probability')
    case_completion = request.get_json().get('case_completion')
    try:
        file = files.find_one({"_id": ObjectId(file_id)})
    except:
        return Response(f'File with {file_id} not found',404)
    event_log_id = file.get('event_log_id')
    res = requests.post(PRCORE_BASE_URL + '/project', 
                        headers=PRCORE_HEADERS, 
                        json={
                                'event_log_id': event_log_id,
                                'positive_outcome': [[positive_outcome]],
                                'treatment': [[treatment]]
                                })
    try:
        res_dict = res.json()
        project_id = res_dict.get('project',{}).get('id')
    except:
        print(res)
        return Response('Something went wrong with PrCore',500)
    files.find_one_and_update({"_id": ObjectId(file_id)},
                                {"$set": {
                                    "project_id": project_id,
                                    "positive_outcome": positive_outcome,
                                    "treatment": treatment,
                                    "alarm_probability": alarm_probability,
                                    "case_completion": case_completion}})
    return Response('Parameters saved successfully',200)

@app.route('/eventlogs')
def get_eventlogs():
    try: 
        fs = files.find({})
        logs = [{"_id": str(log.get('_id')),
                'filename': log.get('filename'), 
                'datetime': log.get('datetime'),
                'positiveOutcome': log.get('positive_outcome'),
                'treatment': log.get('treatment'),
                'alarmProbability': log.get('alarm_probability'),
                'caseCompletion' : log.get('case_completion')} for log in fs]
        return jsonify(eventlogs = logs)
    except:
        return Response("Event logs not found",404)

@app.route('/eventlogs/<file_id>')
def get_eventlog(file_id):
    try:
        log = files.find_one({"_id": ObjectId(file_id)})
        log['_id'] = str(log.get('_id'))
        return jsonify(eventlog = log)
    except:
        return Response(f'Event log with {file_id} not found',404)

@app.route('/cases')
def get_cases():
    global kpi
    c = cases.find({})
    return jsonify(kpi = kpi, cases = list(c))

@app.route('/cases/<case_id>')
def get_case(case_id):
    global kpi
    c = [obj for obj in list(cases.find({})) if str(obj.get("_id")) == str(case_id)][0]
    return jsonify(kpi = kpi, case = c)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

