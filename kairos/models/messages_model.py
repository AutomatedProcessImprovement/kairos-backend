from werkzeug.local import LocalProxy
from kairos.models.db import get_db

db = LocalProxy(get_db)

def get_messages():
    return list(db.messages.find({'context': False},{'_id': False}))

def get_messages_by_log_id(event_log_id):
    return list(db.messages.find({'context': False, 'event_log_id': int(event_log_id)},{'_id': False}))

def get_messages_by_case_id(case_id):
    return list(db.messages.find({'context': False, 'case_id': case_id},{'_id': False}))

def get_context():
    return list(db.messages.find({},{'_id': False,'context': False, 'event_log_id': False, 'case_id': False}))

def get_context_by_log_id(event_log_id):
    return list(db.messages.find({'event_log_id': int(event_log_id)},{'_id': False,'context': False, 'event_log_id': False, 'case_id': False}))

def get_context_by_case_id(case_id):
    return list(db.messages.find({'case_id': case_id},{'_id': False,'context': False, 'event_log_id': False, 'case_id': False}))

def save_message(role,content,context=False,event_log_id=None,case_id=None):
    new_message = {
        'role': role,
        'content': content,
        'context': context,
        'event_log_id': event_log_id,
        'case_id': case_id
    }
    return db.messages.insert_one(new_message)

def count_messages():
    return db.messages.count_documents({'context': False})

def delete_messages():
    return db.messages.deleteMany({})

def get_system_messages():
    return list(db.messages.find({'role': 'system'}))
