from werkzeug.local import LocalProxy
from kairos.models.db import get_db

db = LocalProxy(get_db)

def get_event_logs():
    try:
        return list(db.files.find({}))
    except Exception as e:
        return e


def get_event_log(file_id):
    try:
        log = db.files.find_one({"_id": int(file_id)})
        return log
    except (StopIteration) as _:
        return None
    except Exception as e:
        return e

def save_event_log(filename, event_log_id, columns_header,columns_definition,columns_data,delimiter,datetime):
    event_log = {
        '_id':event_log_id,
        'filename':filename,
        'columns_header':columns_header,
        'columns_definition': columns_definition,
        'columns_data':columns_data,
        'delimite':delimiter,
        'datetime':datetime
        }
    return db.files.insert_one(event_log)
    
def update_event_log(file_id,data):
    try:
        response = db.files.find_one_and_update({"_id": int(file_id)},{"$set": data})
        return response
    except Exception as e:
        return e