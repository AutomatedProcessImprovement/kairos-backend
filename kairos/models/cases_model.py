from werkzeug.local import LocalProxy
from bson.objectid import ObjectId
from kairos.models.db import get_db

db = LocalProxy(get_db)

def get_cases():
    try:
        return list(db.cases.find({}))
    except Exception as e:
        return e

def get_cases_by_log(file_id):
    try:
        return list(db.cases.find({"file_id": int(file_id)}))
    except Exception as e:
        return e

def get_case_by_log(file_id,case_id):
    try:
        return list(db.cases.find({"file_id":file_id,"_id":int(case_id)}))
    except Exception as e:
        return e

def get_case(case_id):
    try:
        c = db.cases.find_one({"_id": int(case_id)})
        return c
    except (StopIteration) as _:
        return None
    except Exception as e:
        return e
    
def save_case(case):
    return db.cases.cases.insert_one(case)

def update_case(case_id,data):
    try:
        response = db.cases.cases.find_one_and_update({"_id": int(case_id)},{"$set": data})
        return response
    except Exception as e:
        return e
