from flask import request, jsonify, current_app

import kairos.models.messages_model as messages_db
import kairos.utils.llamaindex as llamaindex_utils

def get_messages_for_log(event_log_id):
    try: 
        messages = messages_db.get_messages_by_log_id(event_log_id=event_log_id)
    except Exception as e:
        current_app.logger.error(f'{request.method} {request.path} 500 - {e}')
        return jsonify(error=str(e)),500
    current_app.logger.info(f'{request.method} {request.path} 200')
    return jsonify(memory = messages),200

def get_messages_for_case(event_log_id,case_id):
    try: 
        messages = messages_db.get_messages_by_case_id(case_id=case_id)
    except Exception as e:
        current_app.logger.error(f'{request.method} {request.path} 500 - {e}')
        return jsonify(error=str(e)),500
    current_app.logger.info(f'{request.method} {request.path} 200')
    return jsonify(memory = messages),200

def get_answer(event_log_id,case_id):
    if not event_log_id or not case_id:
        current_app.logger.error('Event log id and case id cannot be null.')
        return jsonify(error='Please specify event_log_id and case_id.'),403
    
    question = request.get_json().get('question')
    if not question:
        current_app.logger.error('Question cannot be null.')
        return jsonify(error='Please specify a question.'),403
    
    answer = llamaindex_utils.ask_ai(question, event_log_id)
    messages_db.save_message(role='user',content=question,event_log_id=event_log_id,case_id=case_id)
    messages_db.save_message(role='assistant',content=answer,event_log_id=event_log_id,case_id=case_id)
    
    current_app.logger.info(f'{request.method} {request.path} 200')
    return jsonify(answer = answer),200
