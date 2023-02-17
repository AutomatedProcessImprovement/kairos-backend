from werkzeug.local import LocalProxy
from kairos.models.db import get_db

db = LocalProxy(get_db)

def get_cases():
    try:
        return list(db.cases.find({}))
    except Exception as e:
        return e

def get_cases_by_project_id(project_id):
    try:
        return list(db.cases.find({"project_id": int(project_id)}))
    except Exception as e:
        return e

def get_case_by_project_id(case_id,project_id):
    try:
        return db.cases.find_one({"project_id":int(project_id),"_id":case_id})
    except (StopIteration) as _:
        return None
    except Exception as e:
        return e

def get_case(case_id):
    try:
        return db.cases.find_one({"_id": case_id})
    except (StopIteration) as _:
        return None
    except Exception as e:
        return e
    
def save_case(case_id,project_id,case_completed,activity,prescriptions_with_output,case_attributes):
    activity['prescriptions'] = prescriptions_with_output
    new_case = {
        '_id':case_id,
        'project_id':project_id,
        'case_completed':case_completed,
        'activities':[activity],
        'case_attributes':case_attributes,
        }
    return db.cases.insert_one(new_case)

def update_case(case_id,case_completed,activity,prescriptions_with_output):
    activity['prescriptions'] = prescriptions_with_output
    try:
        response = db.cases.find_one_and_update(
            {"_id": case_id},
            {
                "$set": { 'case_completed':case_completed},
                "$push":{'activities': activity}
            },
        )
        return response
    except Exception as e:
        return e

