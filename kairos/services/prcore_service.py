import json

import requests
import sseclient
from flask import current_app

import kairos.services.utils as k_utils

def upload_file(file, delimiter):
    res = requests.post(current_app.config.get('PRCORE_BASE_URL') + '/event_log', 
                        files={'file': (file.filename, file.stream, file.content_type)}, 
                        data={"separator": str(delimiter)}, 
                        headers=current_app.config.get('PRCORE_HEADERS'))
    try:
        return res.json()
    except Exception as e:
        return e
    
def define_columns(event_log_id,data):
    res = requests.put(current_app.config.get('PRCORE_BASE_URL') + f'/event_log/{event_log_id}', 
                       json={'columns_definition':data}, 
                       headers=current_app.config.get('PRCORE_HEADERS'))
    try:
        return res.json()
    except Exception as e:
        return e

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
    try:
        # print(res.json())
        return res.json().get('project',{}).get('id')
    except Exception as e:
        return e

def delete_project(project_id):
    # print(project_id)
    res = requests.delete(current_app.config.get('PRCORE_BASE_URL') + f'/project/{project_id}', headers=current_app.config.get('PRCORE_HEADERS'))
    try:
        # print(res.json())
        return res.json()
    except Exception as e:
        # print(res)
        return e

def get_project_status(project_id):
    # print(project_id)
    res = requests.get(current_app.config.get('PRCORE_BASE_URL') + f'/project/{project_id}', headers=current_app.config.get('PRCORE_HEADERS'))
    try:
        # print(res.json())
        return res.json().get('project',{}).get('status')
    except Exception as e:
        print(res)
        return e

def start_simulation(project_id):
    res = requests.put(current_app.config.get('PRCORE_BASE_URL') + f'/project/{project_id}/stream/start/simulating', headers=current_app.config.get('PRCORE_HEADERS'))
    try:
        return res.json()
    except Exception as e:
        return e

def stop_simulation(project_id):
    res = requests.put(current_app.config.get('PRCORE_BASE_URL') + f'/project/{project_id}/stream/stop', headers=current_app.config.get('PRCORE_HEADERS'))
    try:
        return res.json()
    except Exception as e:
        return e 

def clear_streamed_data(project_id):
    res = requests.put(current_app.config.get('PRCORE_BASE_URL') + f'/project/{project_id}/stream/clear', headers=current_app.config.get('PRCORE_HEADERS'))
    try:
        return res.json()
    except Exception as e:
        return e 

def start_stream(project_id):
    print(f'Starting the stream for project Id: {project_id}')
    response = requests.get(current_app.config.get('PRCORE_BASE_URL') + f'/project/{project_id}/stream/result', headers=current_app.config.get('PRCORE_HEADERS'), stream=True)
    print(f'got response: {response}')
    try:
        client = sseclient.SSEClient(response)
    except Exception as e:
        return e

    print("Waiting for events...")

    try:
        for event in client.events():
            if event.event != "message":
                continue

            event_data = json.loads(event.data)
            first_event = event_data[0]
            print(f"Received message: {event.event}")
            print(f"ID: {event.id}")

            print(f"Data type: {type(event_data)}")
            print(f"Length: {len(event_data)}")
            # print(first_event)

            try:
                k_utils.record_event(first_event,event.id,project_id)
            except Exception as e:
                return e

            print("-" * 24)
    except KeyboardInterrupt:
        print("Interrupted by user")

    print("Done!")
