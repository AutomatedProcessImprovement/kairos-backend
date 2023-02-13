from flask import current_app,Blueprint, request, jsonify
import kairos.db as k_db
import kairos.prcore as prcore

from flask_cors import CORS
import kairos.utils as k_utils
from datetime import datetime


routes_api = Blueprint('routes')

CORS(routes_api)

@routes_api.route('/upload', methods=['POST'])
def save_file():
    if 'file' not in request.files:
        return jsonify(error = 'File not found'), 400
    
    file = request.files['file']
    if not file and not k_utils.is_allowed_file(file.filename):
        return jsonify(error='Incorrect file extension'), 400
    
    delimiter = request.form.get('delimiter')

    try:
        res = prcore.upload_file(file, delimiter)
    except Exception as e:
        return jsonify(error=str(e)), 400
    event_log_id = res.get('event_log_id')
    k_db.save_event_log(file.filename, event_log_id, res.get('columns_header'), res.get('columns_inferred_definition'),
                                 res.get('columns_data'), delimiter, datetime.datetime.now())
    return jsonify(fileId = str(event_log_id)), 200

@routes_api.route('/update/<event_log_id>', methods=['PUT'])
def update_types(event_log_id):
    types = request.get_json().get('types')
    case_attributes = request.get_json().get('case_attributes')

    try:
        file = get_event_log(event_log_id)
    except Exception as e:
        return jsonify(error = str(e)), 400
    
    try:
        res = prcore.define_columns(event_log_id,types)
    except Exception as e:
        jsonify(error=str(e)),400
    
    activities = list(res.get('activities_count').keys())
    dic = k_utils.get_case_attributes(file,case_attributes)
    k_db.update_event_log( event_log_id,{
                                        "activities": activities,
                                        "columns_definition": types,
                                        "case_attributes": dic,
                                        "outcome_selections": res.get('outcome_selections'),
                                        "treatment_selections": res.get('treatment_selections')})
    return jsonify(message='Types updated successfully'),200

@routes_api.route('/parameters/<file_id>', methods=['POST'])
def define_parameters(file_id):
    positive_outcome = request.get_json().get('positive_outcome')
    treatment = request.get_json().get('treatment')
    alarm_probability = request.get_json().get('alarm_probability')
    case_completion = request.get_json().get('case_completion')
    try:
        file = k_db.get_event_log(file_id)
    except Exception as e:
        return jsonify(error = str(e)), 400
    
    event_log_id = file.get('event_log_id')   
    project_id = file.get('project_id')
    
    try:
        res = prcore.define_parameters(project_id,event_log_id,positive_outcome,treatment)
    except Exception as e:
        return jsonify(error=str(e)),400
    
    project_id = res.get('project',{}).get('id')
    k_db.update_event_log(file_id,{
                            "project_id": project_id,
                            "positive_outcome": positive_outcome,
                            "treatment": treatment,
                            "alarm_probability": alarm_probability,
                            "case_completion": case_completion
                            })
    return jsonify(message='Parameters saved successfully'),200

@routes_api.route('/project/<file_id>/status')
def get_project_status(file_id):
    try:
        log = k_db.get_event_log(file_id)
    except Exception as e:
        return jsonify(error = str(e)), 400
    
    project_id = log.get('project_id')
    try:
        res = prcore.check_project_status(project_id)
    except Exception as e:
        return jsonify(error=str(e)),400
    
    status = res.get('project',{}).get('status')
    return jsonify(status = status),200


@routes_api.route('/event_logs')
def get_event_logs():
    try: 
        logs = k_db.get_event_logs()
        return jsonify(event_logs = logs),200
    except Exception as e:
        return jsonify(error=str(e)),400

@routes_api.route('/event_logs/<file_id>')
def get_event_log(file_id):
    try:
        log = k_db.get_event_log(file_id)
        return jsonify(event_log = log),200
    except Exception as e:
        return jsonify(error=str(e)),400
    
@routes_api.route('/cases')
def get_cases():
    try:
        c = k_db.get_cases()
        return jsonify(cases = list(c))
    except Exception as e:
        return jsonify(error=str(e)),400
    
@routes_api.route('event_log/<file_id>/cases')
def get_cases_by_log(file_id):
    try:
        f = k_db.get_event_log(file_id)
        c = k_db.get_cases_by_log(file_id)
        return jsonify(cases = list(c),kpi=f.get('positive_outcome')),200
    except Exception as e:
        return jsonify(error=str(e)),400

@routes_api.route('/cases/<case_id>')
def get_case(case_id):
    try:
        c = k_db.get_case(case_id)
        return jsonify(case = c)
    except Exception as e:
        return jsonify(error=str(e)),400
