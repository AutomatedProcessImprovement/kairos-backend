from flask import current_app
import requests

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

def check_project_status(project_id):
    res = requests.get(current_app.config.get('PRCORE_BASE_URL') + f'/project/{project_id}', headers=current_app.config.get('PRCORE_HEADERS'))
    try:
        return res.json()
    except Exception as e:
        return e