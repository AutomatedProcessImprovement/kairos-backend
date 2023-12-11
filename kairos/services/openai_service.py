from flask import request, jsonify, current_app

import kairos.utils.ai_assistant as ai_utils

def get_messages_for_case(event_log_id,case_id):
    try: 
        messages = ai_utils.get_messages_by_case_id(case_id=case_id)
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
    
    try:
        answer = ai_utils.ask_ai(case_id,event_log_id,question)
    except Exception as e:
        current_app.logger.error(f'{request.method} {request.path} 400 - {e}')
        return jsonify(error=str(e)),400

    current_app.logger.info(f'{request.method} {request.path} 200')
    return jsonify(answer = answer),200

def delete_thread(event_log_id,case_id):
    if not event_log_id or not case_id:
        current_app.logger.error('Event log id and case id cannot be null.')
        return jsonify(error='Please specify event_log_id and case_id.'),403
    
    try:
        ai_utils.delete_case_thread_id(case_id)
    except Exception as e:
        current_app.logger.error(f'{request.method} {request.path} 400 - {e}')
        return jsonify(error=str(e)),400

    current_app.logger.info(f'{request.method} {request.path} 200')
    return jsonify(message = 'Thread successfully deleted.'),200

def modify_assistant():
    try:
        ai_utils.modify_assistant()
    except Exception as e:
        current_app.logger.error(f'{request.method} {request.path} 400 - {e}')
        return jsonify(error=str(e)),400

    current_app.logger.info(f'{request.method} {request.path} 200')
    return jsonify(message = 'Assistant successfully updated.'),200
