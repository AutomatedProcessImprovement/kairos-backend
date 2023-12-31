import json

import requests
import sseclient
from flask import current_app

import kairos.services.utils as k_utils

def response(res,status=False,json=True):
    if res.status_code != 200:
        print(f'Error in core: {res}')
        if status:
            return 'NULL'
        raise Exception(res)
    if not json:
        return res
    return res.json().get('project',{}).get('status') if status else res.json()

def upload_file(logs, delimiter):
    res = requests.post(current_app.config.get('PRCORE_BASE_URL') + '/event_log', 
                        files=logs, 
                        data={"separator": str(delimiter)}, 
                        headers=current_app.config.get('PRCORE_HEADERS'))
    return response(res)
    
def define_columns(event_log_id,data):
    res = requests.put(current_app.config.get('PRCORE_BASE_URL') + f'/event_log/{event_log_id}', 
                       json={'columns_definition':data}, 
                       headers=current_app.config.get('PRCORE_HEADERS'))
    return response(res)

    
def define_parameters(project_id,event_log_id,positive_outcome,treatment):
    data = {
            'event_log_id': event_log_id,
            'positive_outcome': [[positive_outcome]],
            'treatment': [[treatment]]
            }
    if project_id:
        res = requests.put(current_app.config.get('PRCORE_BASE_URL') + f'/project/{project_id}/definition', 
                        headers=current_app.config.get('PRCORE_HEADERS'), 
                        json=data)
    else:
        res = requests.post(current_app.config.get('PRCORE_BASE_URL') + '/project', 
                        headers=current_app.config.get('PRCORE_HEADERS'), 
                        json=data)
    return response(res)

def delete_project(project_id):
    res = requests.delete(current_app.config.get('PRCORE_BASE_URL') + f'/project/{project_id}', headers=current_app.config.get('PRCORE_HEADERS'))
    return response(res)

def get_project_status(project_id):
    res = requests.get(current_app.config.get('PRCORE_BASE_URL') + f'/project/{project_id}', headers=current_app.config.get('PRCORE_HEADERS'))
    return response(res,True)


def start_simulation(project_id):
    res = requests.put(current_app.config.get('PRCORE_BASE_URL') + f'/project/{project_id}/stream/start/simulating', headers=current_app.config.get('PRCORE_HEADERS'))
    return response(res)

def stop_simulation(project_id):
    res = requests.put(current_app.config.get('PRCORE_BASE_URL') + f'/project/{project_id}/stream/stop', headers=current_app.config.get('PRCORE_HEADERS'))
    return response(res)

def clear_streamed_data(project_id):
    res = requests.put(current_app.config.get('PRCORE_BASE_URL') + f'/project/{project_id}/stream/clear', headers=current_app.config.get('PRCORE_HEADERS'))
    return response(res)


def start_stream(project_id):
    print(f'Starting the stream for project: {project_id}')
    res = requests.get(current_app.config.get('PRCORE_BASE_URL') + f'/project/{project_id}/stream/result', headers=current_app.config.get('PRCORE_HEADERS'), stream=True)
    print(f'got response: {response(res,json=False)}')
    client = sseclient.SSEClient(res)

    print("Waiting for events...")

    for event in client.events():
        if event.event != "message":
            continue

        event_data = json.loads(event.data)
        first_event = event_data[0]
        # print(f"ID: {event.id}")

        case_id = k_utils.record_event(first_event,event.id,project_id)
        
        # print("-" * 24)


def get_static_results(project_id,result_key):
    res = requests.get(current_app.config.get('PRCORE_BASE_URL') + f'/project/{project_id}/result/{result_key}', headers=current_app.config.get('PRCORE_HEADERS'))
    res_json = response(res)
    message = res_json.get('message')
    k_utils.record_results(project_id,res_json)
    return message