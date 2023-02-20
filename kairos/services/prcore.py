import json
import time
import threading

import requests
import sseclient
from flask import current_app

from kairos.models.cases_model import ( get_case_by_project_id, save_case, update_case, update_case_prescriptions)
from kairos.models.event_logs_model import get_event_log_by_project_id


def upload_file(file, delimiter):
    res = requests.post(current_app.config.get('PRCORE_BASE_URL') + '/event_log', 
                        files={'file': (file.filename, file.stream, file.content_type), 'separator': delimiter}, headers=current_app.config.get('PRCORE_HEADERS'))
    try:
        return res.json()
    except Exception as e:
        return e
    
def define_columns(event_log_id,data):
    res = requests.put(current_app.config.get('PRCORE_BASE_URL') + f'/event_log/{event_log_id}', json=data, headers=current_app.config.get('PRCORE_HEADERS'))
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
        return res.json()
    except Exception as e:
        return e

def get_project_status(project_id):
    res = requests.get(current_app.config.get('PRCORE_BASE_URL') + f'/project/{project_id}', headers=current_app.config.get('PRCORE_HEADERS'))
    try:
        return res.json().get('project',{}).get('status')
    except Exception as e:
        return e

def start_simulation(project_id):
    res = requests.put(current_app.config.get('PRCORE_BASE_URL') + f'/project/{project_id}/simulate/start', headers=current_app.config.get('PRCORE_HEADERS'))
    try:
        return res.json()
    except Exception as e:
        return e

def stop_simulation(project_id):
    res = requests.put(current_app.config.get('PRCORE_BASE_URL') + f'/project/{project_id}/simulate/stop', headers=current_app.config.get('PRCORE_HEADERS'))
    try:
        return res.json()
    except Exception as e:
        return e

def start_stream_thread(project_id):
    t = threading.Thread(target=start_stream, args=(project_id,current_app.config.get('PRCORE_BASE_URL'),current_app.config.get('PRCORE_HEADERS')))
    t.start()   

def start_stream(project_id):
    print(f'Starting the stream for project Id: {project_id}')
    response = requests.get(current_app.config.get('PRCORE_BASE_URL') + f'/project/{project_id}/streaming/result', headers=current_app.config.get('PRCORE_HEADERS'), stream=True)
    print(f'got response: {response}')
    try:
        client = sseclient.SSEClient(response)
    except Exception as e:
        return e

    print("Waiting for events...")

    try:
        for event in client.events():
            if event.event == "ping":
                continue

            event_data = json.loads(event.data)
            first_event = event_data[0]
            print(f"Received message: {event.event}")
            print(f"ID: {event.id}")

            print(f"Data type: {type(event_data)}")
            print(f"Length: {len(event_data)}")

            # pprint.pprint(first_event, width=120)

            record_event(first_event,event.id,project_id)

            print("-" * 24)
    except KeyboardInterrupt:
        print("Interrupted by user")

    print("Done!")

def record_event(event_data,event_id,project_id):
    print('Recording event...')
    try:
        log = get_event_log_by_project_id(project_id)
    except Exception as e:
        print(str(e))
        return
    columns_definition = log.get("columns_definition")
    case_attributes_definition = log.get('case_attributes')

    case_id = 0
    activity = {'event_id': event_id}
    case_attributes = {}

    for k,v in event_data.get('data').items():
        attr = columns_definition.get(k)
        if attr == 'CASE_ID':
            case_id = v.split('-')[1]
        elif attr == 'ACTIVITY':
            activity['ACTIVITY'] = v
        elif attr in ['TIMESTAMP','START_TIMESTAMP']:
            activity['TIMESTAMP'] = v
        elif k in case_attributes_definition:
            case_attributes[k] = v
        else:
            activity[k] = v

    prescriptions = event_data.get("prescriptions")
    prescriptions_with_output = [prescriptions[p] for p in prescriptions if prescriptions[p]["output"]]
    case_completed = event_data.get('case_completed')

    try:
        old_case = get_case_by_project_id(case_id,project_id)
    except Exception as e:
        return e

    if not old_case:
        _id = save_case(case_id,project_id,case_completed,activity,prescriptions_with_output,case_attributes).inserted_id
        print(f'saved case: {_id}')
    else:
        event_id = old_case['activities'][-1]['event_id']
        update_case_prescriptions(case_id,event_id,activity['ACTIVITY'])
        time.sleep(1)
        update_case(case_id,case_completed,activity,prescriptions_with_output)
        print(f'updated case: {case_id}')

    return
