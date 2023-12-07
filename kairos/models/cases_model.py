from werkzeug.local import LocalProxy
from kairos.models.db import get_db
from pymongo import ReturnDocument


db = LocalProxy(get_db)

def get_cases():
    return list(db.cases.find({}))

def get_cases_by_log_id(event_log_id):
    return list(db.cases.find({"event_log_id": int(event_log_id)}))

def get_cases_by_log_id_and_completion(event_log_id, case_completed):
    return list(db.cases.find({"event_log_id": int(event_log_id), "case_completed": case_completed}))

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

def update_case_thread_id(case_id,thread_id):
    response = db.cases.find_one_and_update(
        {"_id": case_id},
        {
            "$set": {'thread_id': thread_id},
        },
        return_document=ReturnDocument.AFTER
    )
    if not response:
        raise Exception(f'No case found with ID {case_id}') 
    return response

def get_case_thread_id(case_id):
    response = db.cases.aggregate(
        [{'$match': {'_id': case_id}}, {'$project': {'thread_id': 1, '_id': 0}}]
    )
    if not response:
        raise Exception(f'No case found with ID {case_id}') 
    return list(response)[0].get('thread_id')


def get_case_structure(case_id):
    response = db.cases.aggregate(
        [
            {'$match': { '_id': case_id }},
            {'$unwind': "$activities"},
            {'$project': {
                '_id': 1,
                'event_log_id': 1,
                'case_completed': 1,
                'case_attributes': 1,
                'case_performance': 1,
                'activities': 1,
                'numPrescriptions': { '$size': "$activities.prescriptions" }
            } },
            {
                '$sort': { 'numPrescriptions': -1 }
            },
            {
                '$group': {
                    '_id': "$_id",
                    'event_log_id': { '$first': "$event_log_id" },
                    'case_completed': { '$first': "$case_completed" },
                    'case_attributes': { '$first': "$case_attributes" },
                    'case_performance': { '$first': "$case_performance" },
                    'activities': { '$first': "$activities" }
                }
            }
        ]
    )
    if not response:
        raise Exception(f'No case found with ID {case_id}') 
    return list(response)[0]