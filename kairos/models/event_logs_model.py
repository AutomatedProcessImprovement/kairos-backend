from werkzeug.local import LocalProxy
from kairos.models.db import get_db

db = LocalProxy(get_db)

def get_event_logs():
    return list(db.files.find({}))


def get_event_log(event_log_id):
    log = db.files.find_one({"_id": int(event_log_id)})
    if log == None:
        raise Exception(f'No log found with ID {event_log_id}')
    return log
    

def get_event_log_by_project_id(project_id):
    log = db.files.find_one({"project_id": project_id})
    if not log:
        raise Exception(f'No log found with project ID {project_id}')
    return log

def save_event_log(event_log_id,filename , columns_header,columns_definition,columns_data,delimiter,datetime, test_filename):
    event_log = {
        '_id':event_log_id,
        'filename':filename,
        'test_filename': test_filename,
        'columns_header':columns_header,
        'columns_definition': columns_definition,
        'columns_data':columns_data,
        'delimiter':delimiter,
        'datetime':datetime
        }
    return db.files.insert_one(event_log)
    
def update_event_log(event_log_id,data):
    response = db.files.find_one_and_update({"_id": int(event_log_id)},{"$set": data})
    if not response:
        raise Exception(f'No log found with ID {event_log_id}') 
    return response

    
def delete_event_log(event_log_id):
    response = db.files.delete_one({"_id": int(event_log_id)})
    if not response:
        raise Exception(f'No log found with ID {event_log_id}') 

def get_event_log_structure(event_log_id):
    response = db.files.aggregate(
        [
            {'$match': { '_id': event_log_id }},
            {'$project': {
                '_id': 1,
                'filename': 1,
                'number_of_cases': 1,
                'columns_definition': 1,
                'cost_units': 1,
                'case_completion': 1,
                'alarm_threshold': 1,
                'positive_outcome': 1,
                'treatment': 1,
            } }
        ]
    )
    if not response:
        raise Exception(f'No log found with ID {event_log_id}') 
    return list(response)