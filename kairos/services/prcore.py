from flask import current_app
import requests
import json
import pprint
import sseclient

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
    res = requests.get(current_app.config.get('PRCORE_BASE_URL') + f'/project/{project_id}/simulate/start', headers=current_app.config.get('PRCORE_HEADERS'))
    try:
        return res.json()
    except Exception as e:
        return e

def stop_simulation(project_id):
    res = requests.get(current_app.config.get('PRCORE_BASE_URL') + f'/project/{project_id}/simulate/stop', headers=current_app.config.get('PRCORE_HEADERS'))
    try:
        return res.json()
    except Exception as e:
        return e

def start_stream(project_id):
    print(f'Starting the stream for project Id: {project_id}')
    response = requests.get(current_app.config.get('PRCORE_BASE_URL') + f"/project/{project_id}/streaming/result", stream=True, headers=current_app.config.get('PRCORE_HEADERS'))
    print('got response: ')
    print(response)
    client = sseclient.SSEClient(response)

    print("Waiting for events...")

    try:
        for event in client.events():
            if event.event == "ping":
                continue

            event_data = json.loads(event.data)
            first_event = event_data[0]
            print(f"first event: {first_event}")
            prescriptions = first_event["prescriptions"]
            prescriptions_with_output = [prescriptions[p] for p in prescriptions if prescriptions[p]["output"]]

            if not prescriptions_with_output:
                continue
            
            print(f"Received message: {event.event}")
            print(f"ID: {event.id}")


            print(f"Data type: {type(event_data)}")
            print(f"Length: {len(event_data)}")

            pprint.pprint(prescriptions_with_output, width=120)

            print("-" * 24)
    except KeyboardInterrupt:
        print("Interrupted by user")

    print("Done!")
