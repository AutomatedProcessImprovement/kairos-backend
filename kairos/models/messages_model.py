from werkzeug.local import LocalProxy
from kairos.models.db import get_db

db = LocalProxy(get_db)

def get_messages():
    return list(db.messages.find({'_id': False}))

def save_message(content):
    return db.messages.insert_one(content)

def count_messages():
    return db.messages.count_documents({})

def delete_messages():
    return db.messages.deleteMany({})
