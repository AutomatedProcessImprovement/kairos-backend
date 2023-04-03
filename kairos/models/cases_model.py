from werkzeug.local import LocalProxy
from kairos.models.db import get_db
from pymongo import ReturnDocument


db = LocalProxy(get_db)

def get_cases():
    return list(db.cases.find({}))

def get_cases_by_log_id(event_log_id):
    return list(db.cases.find({"event_log_id": int(event_log_id)}))

def delete_cases_by_log_id(event_log_id):
    return db.cases.delete_many({"event_log_id": int(event_log_id)})

def get_case_by_log_id(case_id,event_log_id):
    c = db.cases.find_one({"event_log_id":int(event_log_id),"_id":case_id})
    if c == None:
        raise Exception(f'No case found with ID {case_id} and event log {event_log_id}')
    return c

def get_case(case_id):
    c = db.cases.find_one({"_id": case_id})
    if c == None:
        raise Exception(f'No case found with ID {case_id}')
    return c
    
def save_case(case_id,event_log_id,case_completed,activities,case_attributes):
    new_case = {
        '_id':case_id,
        'event_log_id':event_log_id,
        'case_completed':case_completed,
        'activities':activities,
        'case_attributes':case_attributes,
        }
    return db.cases.insert_one(new_case)

def update_case(case_id,case_completed,activity):
    response = db.cases.find_one_and_update(
        {"_id": case_id},
        {
            "$set": { 'case_completed':case_completed},
            "$push":{'activities': activity}
        },
        return_document=ReturnDocument.AFTER
    )
    if not response:
        raise Exception(f'No case found with ID {case_id}') 
    return response


def update_case_prescriptions(case_id,new_activities):
    db.cases.update_many(
        {"_id": case_id},
        {
            "$set": {'activities': new_activities},
        },
        upsert=False
    )

    
def update_case_performance(case_id,case_performance):
    response = db.cases.find_one_and_update(
        {"_id": case_id},
        {"$set": {'case_performance': case_performance}},
    )
    if not response:
        raise Exception(f'No case found with ID {case_id}') 
    return response

def get_prescriptions(event_log_id):
    prescriptions = db.cases.find({"event_log_id": int(event_log_id)},{'activities': {'$slice': -1},'case_performance': 1})
    return list(prescriptions)