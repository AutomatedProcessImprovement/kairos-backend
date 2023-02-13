from flask import current_app,g
from flask_pymongo import PyMongo
from werkzeug.local import LocalProxy
from bson.objectid import ObjectId
from pymongo.errors import DuplicateKeyError, OperationFailure

def get_db():
    """
    Configuration method to return db instance
    """

    db = getattr(g, "_database", None)

    if db is None:
        db = g._database = PyMongo(current_app).db
       
    return db

db = LocalProxy(get_db)

def get_cases():
    try:
        return list(db.cases.find({}))
    except Exception as e:
        return e

def get_cases_by_log(file_id):
    try:
        return list(db.cases.find({"file_id":file_id}))
    except Exception as e:
        return e

def get_case(case_id):
    try:
        c = [obj for obj in list(db.cases.find({})) if str(obj.get("_id")) == str(case_id)]
        if not c:
            return None
        return c[0]
    except (StopIteration) as _:
        return None
    except Exception as e:
        return e
    
def save_case(case):
    return db.cases.insert_one(case)

def update_case(case_id,data):
    try:
        response = db.cases.find_one_and_update({"_id": ObjectId(case_id)},{"$set": data})
        return response
    except Exception as e:
        return e

def get_event_logs():
    try:
        return list(db.files.find({}))
    except Exception as e:
        return e


def get_event_log(event_log_id):
    try:
        log = db.files.find_one({"event_log_id": event_log_id})
        return log
    except (StopIteration) as _:
        return None
    except Exception as e:
        return e

def save_event_log(filename, event_log_id, columns_header,columns_definition,columns_data,delimiter,datetime):
    event_log = {
        'filename':filename,
        'event_log_id':event_log_id,
        'columns_header':columns_header,
        'columns_definition': columns_definition,
        'columns_data':columns_data,
        'delimite':delimiter,
        'datetime':datetime
        }
    return db.files.insert_one(event_log)
    
def update_event_log(event_log_id,data):
    try:
        response = db.files.find_one_and_update({"event_log_id": event_log_id},{"$set": data})
        return response
    except Exception as e:
        return e