from flask import Blueprint, request, jsonify, current_app
from flask_cors import CORS

from datetime import datetime

import kairos.models.event_logs_model as event_logs_db
import kairos.services.prcore as prcore
import kairos.api.utils as k_utils

event_logs_api = Blueprint('event_logs_api','event_logs_api',url_prefix='/api')

CORS(event_logs_api)

@event_logs_api.route('/event_logs')
def get_event_logs():
    try: 
        logs = event_logs_db.get_event_logs()
        return jsonify(event_logs = logs),200
    except Exception as e:
        return jsonify(error=str(e)),400

@event_logs_api.route('/event_logs/<file_id>')
def get_event_log(file_id):
    try:
        log = event_logs_db.get_event_log(file_id)
        return jsonify(event_log = log),200
    except Exception as e:
        return jsonify(error=str(e)),400
    
@event_logs_api.route('/event_logs/<file_id>/parameters')
def get_event_log_parameters(file_id):
    try:
        log = event_logs_db.get_event_log(file_id)
        return jsonify(kpi = log['positive_outcome'], caseCompletion = log['case_completion'],treatment = log['treatment'],alarmThreshold = log['alarm_threshold']),200
    except Exception as e:
        return jsonify(error=str(e)),400


@event_logs_api.route('/upload', methods=['POST'])
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
    file_id = event_logs_db.save_event_log(file.filename, event_log_id, res.get('columns_header'), res.get('columns_inferred_definition'),
                                 res.get('columns_data'), delimiter, datetime.now()).inserted_id
    
    return jsonify(fileId = str(file_id)), 200

@event_logs_api.route('/update/<file_id>', methods=['PUT'])
def update_types(file_id):
    columns_definition = request.get_json().get('columns_definition')
    case_attributes = request.get_json().get('case_attributes')
    
    try:
        res = prcore.define_columns(file_id,columns_definition)
    except Exception as e:
        jsonify(error=str(e)),400

    activities = list(res.get('activities_count').keys())
    # TODO save file somewhere and get case attributes properly
    event_logs_db.update_event_log( file_id,{
                                        "activities": activities,
                                        "case_attributes": case_attributes,
                                        "columns_definition": columns_definition,
                                        "outcome_options": res.get('outcome_options'),
                                        "treatment_options": res.get('treatment_options')})
    return jsonify(message='Types updated successfully'),200

@event_logs_api.route('/parameters/<file_id>', methods=['POST'])
def define_parameters(file_id):
    positive_outcome = request.get_json().get('positive_outcome')
    treatment = request.get_json().get('treatment')
    alarm_threshold = request.get_json().get('alarm_threshold')
    case_completion = request.get_json().get('case_completion')
    try:
        file = event_logs_db.get_event_log(file_id)
    except Exception as e:
        return jsonify(error = str(e)), 400
    
    project_id = file.get('project_id')
    
    try:
        res = prcore.define_parameters(project_id,file_id,positive_outcome,treatment)
    except Exception as e:
        return jsonify(error=str(e)),400
    
    project_id = res.get('project',{}).get('id')
    event_logs_db.update_event_log(file_id,{
                            "project_id": project_id,
                            "positive_outcome": positive_outcome,
                            "treatment": treatment,
                            "alarm_threshold": alarm_threshold,
                            "case_completion": case_completion
                            })
    return jsonify(message='Parameters saved successfully'),200

# Project 

@event_logs_api.route('/projects/<file_id>/status')
def get_project_status(file_id):
    try:
        log = event_logs_db.get_event_log(file_id)
    except Exception as e:
        return jsonify(error = str(e)), 400
    if not log:
        return jsonify(error = 'log not found'), 400
    
    project_id = log.get('project_id')
    try:
        res = prcore.get_project_status(project_id)
    except Exception as e:
        return jsonify(error=str(e)),400
    
    return jsonify(status = res),200

@event_logs_api.route('/projects/<file_id>/simulate/start', methods=['PUT'])
def start_simulation(file_id):
    try: 
        log = event_logs_db.get_event_log(file_id)
    except Exception as e:
        print(str(e))
        return jsonify(error = str(e)), 400
    
    project_id = log.get('project_id')
    status = prcore.get_project_status(project_id)
    if status != 'TRAINED':
        return jsonify(message=f'Cannot start the simulation, project status: {status}'), 400
    
    try:
        res = prcore.start_simulation(project_id)
    except Exception as e:
        print(f"error in prcore: {str(e)}")
        return jsonify(error=str(e)),400
    
    status = prcore.get_project_status(project_id)
    print(res)
    print('Project status: ' + status)
    try:
        prcore.start_stream(project_id)
    except Exception as e:
        print(str(e))
        return jsonify(message=str(e)),404
    return jsonify(message = res,status = status)

@event_logs_api.route('/projects/<file_id>/simulate/stop', methods=['PUT'])
def stop_simulation(file_id):
    try: 
        log = event_logs_db.get_event_log(file_id)
    except Exception as e:
        return jsonify(error = str(e)), 400
    
    project_id = log.get('project_id')
    status = prcore.get_project_status(project_id)
    if status not in ['STREAMING','SIMULATING']:
        return jsonify(message=f'Cannot stop the simulation, project status: {status}'), 400
    
    try:
        res = prcore.stop_simulation(project_id)
    except Exception as e:
        return jsonify(error=str(e)),400
    
    status = prcore.get_project_status(project_id)
    print('Simulation stopped! Project status: ' + status)
    return jsonify(message = res,status = status)