from flask import current_app, g
from pymongo import MongoClient
from werkzeug.local import LocalProxy

def get_db():
    """
    Configuration method to return db instance
    """
    db = getattr(g, "_database", None)

    if db is None:

        db = g._database = MongoClient(current_app.config.get('MONGO_URI')).flask_db
       
    return db

def query_db(collection, aggregate:list):
    db = LocalProxy(get_db)
    return db[collection].aggregate(aggregate)

def find_similar_cases(case_id):
    db = LocalProxy(get_db)
    
    caseInstance = db.cases.find_one({"_id": case_id})
    if caseInstance == None:
        current_app.logger.error(f'No case found with id {case_id}.')
        return f'No case found with id {case_id}.'

    return list(db.cases.aggregate([
        {
            "$search": {
                "index": "caseindex",
                "moreLikeThis": {
                    "like": caseInstance
                }
            }
        },
        { "$limit": 4 },
        {
            "$project": {
                "_id": 1,
                "case_completed": 1,
                "event_log_id": 1,
                "case_attributes": 1,
                "case_performance": 1,
                "activities": 1
            }
        }
    ]))[1:]