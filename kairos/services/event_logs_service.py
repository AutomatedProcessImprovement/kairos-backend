from zipfile import BadZipFile
from flask import request, jsonify

from datetime import datetime
import time
import json

import kairos.models.event_logs_model as event_logs_db
import kairos.models.cases_model as cases_db
from kairos.enums.project_status import Status as PROJECT_STATUS
import kairos.services.prcore_service as prcore_service
import kairos.services.utils as k_utils

def get_logs():
    try: 
        logs = event_logs_db.get_event_logs()
    except Exception as e:
        return jsonify(error=str(e)),500
    return jsonify(event_logs = logs),200

def get_log(event_log_id):
    try:
        log = event_logs_db.get_event_log(event_log_id)
    except Exception as e:
        return jsonify(error=str(e)),500
    return jsonify(event_log = log),200
    
def save_log():
    print(request.files)
    if 'file' not in request.files:
        return jsonify(error = 'Log not found'), 400
    
    file = request.files.get('file')
    if not file:
        return jsonify(error='Log cannot be none'), 400
    test_filename = request.files.get('test').filename if request.files.get('test') else None

    files = []
    for k,f in request.files.items():
        if not k_utils.is_allowed_file(f):
            return jsonify(error='Incorrect file extension.'), 400
        files.append(k_utils.format_file(k,f))

    delimiter = request.form.get('delimiter')
    if not delimiter: delimiter = ','

    try:
        res = prcore_service.upload_file(files,delimiter)
        event_log_id = res.get('event_log_id')
        columns_header = res.get('columns_header')
        columns_definition = dict(zip(columns_header, res.get('columns_inferred_definition')))
        columns_data = res.get('columns_data')
    except Exception as e:
        return jsonify(error=str(e)), 500
    try:
        saved_id = event_logs_db.save_event_log(file.filename, event_log_id, columns_header, columns_definition,
                                 columns_data, delimiter, datetime.now(),test_filename).inserted_id
    except Exception as e:
        return jsonify(error = str(e)),500
    
    return jsonify(logId = str(saved_id)), 200


def delete_log(event_log_id):
    try:
        log = event_logs_db.get_event_log(event_log_id)
    except Exception as e:
        return jsonify(error = str(e)), 500
    
    project_id = log.get('project_id')
    if project_id != None:
        try:
            prcore_service.delete_project(project_id)
        except Exception as e:
            jsonify(error=str(e)),400

    try:
        cases_db.delete_cases_by_log_id(event_log_id)
        event_logs_db.delete_event_log(event_log_id)
    except Exception as e:
        return jsonify(error=str(e)),500
    
    return jsonify(message=f'Event log {event_log_id} deleted successfully'),200


def get_log_parameters(event_log_id):
    try:
        log = event_logs_db.get_event_log(event_log_id)
    except Exception as e:
        return jsonify(error=str(e)),500
    parameters = {
        'columnsDefinition': log.get('columns_definition'),
        'columnsDefinitionReverse': log.get('columns_definition_reverse'), 
        'kpi': log.get('positive_outcome'), 
        'caseCompletion': log.get('case_completion'),
        'treatment': log.get('treatment'),
        'alarmThreshold': log.get('alarm_threshold')
    }
    return jsonify(parameters = parameters),200
    

def define_log_column_types(event_log_id):
    try:
        event_logs_db.get_event_log(event_log_id)
    except Exception as e:
        return jsonify(error = str(e)), 400    
    
    columns_definition = request.get_json().get('columns_definition')
    case_attributes = request.get_json().get('case_attributes')
    
    try:
        columns_definition_reverse = k_utils.validate_columns_definition(columns_definition)
    except Exception as e:
        return jsonify(error = str(e)),400

    try:
        res = prcore_service.define_columns(event_log_id,columns_definition)
        activities = list(res.get('activities_count').keys())
        outcome_options = res.get('outcome_options')
        treatment_options = res.get('treatment_options')
    except Exception as e:
        return jsonify(error=str(e)),400

    try:
        event_logs_db.update_event_log( event_log_id,{
                                        "activities": activities,
                                        "case_attributes": case_attributes,
                                        "columns_definition": columns_definition,
                                        "columns_definition_reverse": columns_definition_reverse,
                                        "outcome_options": outcome_options,
                                        "treatment_options": treatment_options})
    except Exception as e:
        return jsonify(error = str(e)),500

    return jsonify(message='Column types updated successfully'),200
    
def define_log_parameters(event_log_id):
    try:
        log = event_logs_db.get_event_log(event_log_id)
    except Exception as e:
        return jsonify(error = str(e)), 400
    
    positive_outcome = request.get_json().get('positive_outcome')
    treatment = request.get_json().get('treatment')
    alarm_threshold = request.get_json().get('alarm_threshold')
    case_completion = request.get_json().get('case_completion')
    parameters_description = request.get_json().get('parameters_description')

    if not all([positive_outcome, treatment, alarm_threshold, case_completion]):
        return jsonify(error='All parameters should be defined'),400
    
    columns_definition = log.get('columns_definition')
    positive_outcome['value'] = k_utils.parse_value(columns_definition.get(positive_outcome['column']) or positive_outcome['column'],positive_outcome['value'])
    treatment['value'] = k_utils.parse_value(columns_definition.get(treatment['column']),treatment['value'])

    project_id = log.get('project_id')
    prcore_outcome = k_utils.format_positive_outcome(positive_outcome)

    try:
        res = prcore_service.define_parameters(project_id,event_log_id,prcore_outcome,treatment)
        project_id = res.get('project',{}).get('id')
        result_key = res.get('result_key')
    except Exception as e:
        return jsonify(error=str(e)),400
    
    event_logs_db.update_event_log(event_log_id,{
                            "project_id": project_id,
                            "positive_outcome": positive_outcome,
                            "treatment": treatment,
                            "alarm_threshold": alarm_threshold,
                            "case_completion": case_completion,
                            "parameters_description": parameters_description,
                            'result_key': result_key
                            })
    return jsonify(message='Parameters saved successfully'),200

def get_log_prescriptions(event_log_id):
    try:
        prescriptions = cases_db.get_prescriptions(event_log_id)
        return jsonify(prescriptions = prescriptions),200
    except Exception as e:
        return jsonify(error=str(e)),500
    

# Project

def get_project_status(event_log_id):
    try:
        log = event_logs_db.get_event_log(event_log_id)
    except Exception as e:
        return jsonify(error = str(e)), 400
    
    project_id = log.get('project_id')
    if project_id == None:
        return jsonify(status = 'NULL'),200
    try:
        status = prcore_service.get_project_status(project_id)
        return jsonify(status = status),200
    except Exception as e:
        return jsonify(error=str(e)),400

def start_simulation(event_log_id):
    try: 
        log = event_logs_db.get_event_log(event_log_id)
    except Exception as e:
        return jsonify(error = str(e)), 400
    
    project_id = log.get('project_id')
    status = prcore_service.get_project_status(project_id)
    print(PROJECT_STATUS.TRAINED)
    if status != PROJECT_STATUS.TRAINED:
        return jsonify(error=f'Cannot start the simulation, project status: {status}'), 400
    
    try:
        res = prcore_service.start_simulation(project_id)
    except Exception as e:
        print(f"error in prcore: {str(e)}")
        return jsonify(error=str(e)),400
    
    status = prcore_service.get_project_status(project_id)
    try:
        prcore_service.start_stream(project_id)
    except Exception as e:
        try:
            prcore_service.stop_simulation(project_id)
        except Exception as ex:
            print(str(ex))
        print(str(e))
        return jsonify(error="Something went wrong. Stopping simulation..."),500
    
    return jsonify(message = res),200

def stop_simulation(event_log_id):
    try: 
        log = event_logs_db.get_event_log(event_log_id)
    except Exception as e:
        return jsonify(error = str(e)), 400
    
    project_id = log.get('project_id')
    status = prcore_service.get_project_status(project_id)
    if status not in [PROJECT_STATUS.STREAMING,PROJECT_STATUS.SIMULATING]:
        return jsonify(error=f'Cannot stop the simulation, project status: {status}'), 400
    
    try:
        res = prcore_service.stop_simulation(project_id)
    except Exception as e:
        return jsonify(error=str(e)),400
    
    status = prcore_service.get_project_status(project_id)
    print('Simulation stopped! Project status: ' + status)
    return jsonify(message = res)

def clear_stream(event_log_id):
    try: 
        log = event_logs_db.get_event_log(event_log_id)
    except Exception as e:
        return jsonify(error = str(e)), 400
    
    project_id = log.get('project_id')

    try:
        prcore_service.clear_streamed_data(project_id)
    except Exception as e:
        return jsonify(error=str(e)),400
    
    try:
        cases_db.delete_cases_by_log_id(event_log_id)
    except Exception as e:
        return jsonify(error=str(e)),500
    
    return jsonify(message = 'Successfully cleared streamed data.'),200