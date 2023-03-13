from flask import request, jsonify

from datetime import datetime

import kairos.models.event_logs_model as event_logs_db
import kairos.services.prcore_service as prcore_service
import kairos.services.utils as k_utils

def get_logs():
    try: 
        logs = event_logs_db.get_event_logs()
        return jsonify(event_logs = logs),200
    except Exception as e:
        return jsonify(error=str(e)),400

def get_log(event_log_id):
    try:
        log = event_logs_db.get_event_log(event_log_id)
        return jsonify(event_log = log),200
    except Exception as e:
        return jsonify(error=str(e)),400

def get_log_parameters(event_log_id):
    try:
        log = event_logs_db.get_event_log(event_log_id)
        return jsonify(columnsDefinition = log['columns_definition'],kpi = log['positive_outcome'], caseCompletion = log['case_completion'],treatment = log['treatment'],alarmThreshold = log['alarm_threshold']),200
    except Exception as e:
        return jsonify(error=str(e)),400
    
def save_log():
    if 'file' not in request.files:
        return jsonify(error = 'File not found'), 400
    
    file = request.files['file']
    if not file and not k_utils.is_allowed_file(file.filename):
        return jsonify(error='Incorrect file extension'), 400
    delimiter = request.form.get('delimiter')
    if not delimiter: delimiter = ','
    
    try:
        res = prcore_service.upload_file(file,delimiter)
        event_log_id = res.get('event_log_id')
        columns_header = res.get('columns_header')
        columns_definition = res.get('columns_inferred_definition')
        columns_data = res.get('columns_data')
    except Exception as e:
        return jsonify(error=str(e)), 400

    saved_id = event_logs_db.save_event_log(file.filename, event_log_id, columns_header, columns_definition,
                                 columns_data, delimiter, datetime.now()).inserted_id
    return jsonify(logId = str(saved_id)), 200

def define_log_column_types(event_log_id):
    columns_definition = request.get_json().get('columns_definition')
    case_attributes = request.get_json().get('case_attributes')

    if not columns_definition:
        return jsonify(message = 'Columns definition cannot be null'),400
    
    try:
        res = prcore_service.define_columns(event_log_id,columns_definition)
        activities = list(res.get('activities_count').keys())
        outcome_options = res.get('outcome_options')
        treatment_options = res.get('treatment_options')
    except Exception as e:
        jsonify(error=str(e)),400

    event_logs_db.update_event_log( event_log_id,{
                                        "activities": activities,
                                        "case_attributes": case_attributes,
                                        "columns_definition": columns_definition,
                                        "outcome_options": outcome_options,
                                        "treatment_options": treatment_options})
    return jsonify(message='Column types updated successfully'),200
    
def define_parameters(event_log_id):
    positive_outcome = request.get_json().get('positive_outcome')
    treatment = request.get_json().get('treatment')
    alarm_threshold = request.get_json().get('alarm_threshold')
    case_completion = request.get_json().get('case_completion')

    if not all([positive_outcome, treatment, alarm_threshold, case_completion]):
        return jsonify('All parameters should be defined'),400
    
    try:
        log = event_logs_db.get_event_log(event_log_id)
    except Exception as e:
        return jsonify(error = str(e)), 400
    
    columns_definition = log.get('columns_definition')
    positive_outcome['value'] = k_utils.validate_timestamp(positive_outcome,columns_definition)
    treatment['value'] = k_utils.validate_timestamp(treatment,columns_definition)

    project_id = log.get('project_id')

    try:
        project_id = prcore_service.define_parameters(project_id,event_log_id,positive_outcome,treatment)
    except Exception as e:
        return jsonify(error=str(e)),400
    
    event_logs_db.update_event_log(event_log_id,{
                            "project_id": project_id,
                            "positive_outcome": positive_outcome,
                            "treatment": treatment,
                            "alarm_threshold": alarm_threshold,
                            "case_completion": case_completion
                            })
    return jsonify(message='Parameters saved successfully'),200

def get_project_status(event_log_id):
    try:
        log = event_logs_db.get_event_log(event_log_id)
    except Exception as e:
        return jsonify(error = str(e)), 400
    if not log:
        return jsonify(error = 'log not found'), 400
    
    project_id = log.get('project_id')
    try:
        res = prcore_service.get_project_status(project_id)
    except Exception as e:
        return jsonify(error=str(e)),400
    
    return jsonify(status = res),200

def start_simulation(event_log_id):
    try: 
        log = event_logs_db.get_event_log(event_log_id)
    except Exception as e:
        print(str(e))
        return jsonify(error = str(e)), 400
    
    project_id = log.get('project_id')
    status = prcore_service.get_project_status(project_id)
    if status != 'TRAINED':
        return jsonify(message=f'Cannot start the simulation, project status: {status}'), 400
    
    try:
        res = prcore_service.start_simulation(project_id)
    except Exception as e:
        print(f"error in prcore: {str(e)}")
        return jsonify(error=str(e)),400
    
    status = prcore_service.get_project_status(project_id)
    print(res)
    try:
        prcore_service.start_stream(project_id)
    except Exception as e:
        print(str(e))
        return jsonify(message=str(e)),404
    return jsonify(message = res,status = status)

def stop_simulation(event_log_id):
    try: 
        log = event_logs_db.get_event_log(event_log_id)
    except Exception as e:
        return jsonify(error = str(e)), 400
    
    project_id = log.get('project_id')
    status = prcore_service.get_project_status(project_id)
    if status not in ['STREAMING','SIMULATING']:
        return jsonify(message=f'Cannot stop the simulation, project status: {status}'), 400
    
    try:
        res = prcore_service.stop_simulation(project_id)
    except Exception as e:
        return jsonify(error=str(e)),400
    
    status = prcore_service.get_project_status(project_id)
    print('Simulation stopped! Project status: ' + status)
    return jsonify(message = res,status = status)