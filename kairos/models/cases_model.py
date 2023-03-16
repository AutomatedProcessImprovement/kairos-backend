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
    return db.cases.find_one({"event_log_id":int(event_log_id),"_id":case_id})

def get_case(case_id):
    return db.cases.find_one({"_id": case_id})
    
def save_case(case_id,event_log_id,case_completed,activity,prescriptions_with_output,case_attributes):
    activity['prescriptions'] = prescriptions_with_output
    new_case = {
        '_id':case_id,
        'event_log_id':event_log_id,
        'case_completed':case_completed,
        'activities':[activity],
        'case_attributes':case_attributes,
        }
    return db.cases.insert_one(new_case)

def update_case(case_id,case_completed,activity,prescriptions_with_output):
    activity['prescriptions'] = prescriptions_with_output
    response = db.cases.find_one_and_update(
        {"_id": case_id},
        {
            "$set": { 'case_completed':case_completed},
            "$push":{'activities': activity}
        },
        return_document=ReturnDocument.AFTER
    )
    return response


def update_case_prescriptions(case_id,event_id,new_activity):
    db.cases.find_one_and_update(
        {"_id": case_id},
        {"$set": {'activities.$[activity].prescriptions.$[prescription].status': 'accepted'}},
        {"arrayFilters": [{'activity.event_id': event_id},{'prescription.type': 'NEXT_ACTIVITY', 'prescription.output': new_activity}]}
    )

    
def update_case_performance(case_id,case_performance):
    db.cases.find_one_and_update(
        {"_id": case_id},
        {"$set": {'case_performance': case_performance}},
    )
