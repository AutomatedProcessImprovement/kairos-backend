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