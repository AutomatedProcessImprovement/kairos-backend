import kairos.utils.openai as openai_utils

from flask import request, jsonify, current_app

def ask_openai_question(event_log_id):
    question = request.get_json().get('question')
    context = request.get_json().get('context')
    if not question:
        current_app.logger.error(f'{request.method} {request.path} 400 - Question for OpenAI cannot be null.')
        return jsonify(error = "Question for OpenAI cannot be null."), 400 
    
    try:
        agent = openai_utils.get_agent(event_log_id)
    except Exception as e:
        current_app.logger.error(f'{request.method} {request.path} 400 - {e}')
        return jsonify(error = str(e)), 400 
    
    if context:
        openai_utils.save_openai_context(input=context,agent=agent)

    try:
        answer = agent.run(question)
    except Exception as e:
        current_app.logger.error(f'{request.method} {request.path} 400 - {e}')
        return jsonify(error = f'OpenAI encountered a problem while returning an answer. Please try again.'), 400 
    
    current_app.logger.info(f'{request.method} {request.path} 200')
    return jsonify(answer = answer), 200 

def get_log_openai_history(event_log_id):
    try:
        agent = openai_utils.get_agent(event_log_id)
    except Exception as e:
        openai_utils.create_python_agent(event_log_id)
        current_app.logger.error(f'{request.method} {request.path} 400 - {e}')
        # return jsonify(error = str(e)), 400 
        return jsonify(memory = {'chat_history': ''}), 200
    
    agent = openai_utils.get_agent(event_log_id)
    memory = agent.memory.load_memory_variables({})
    current_app.logger.info(f'{request.method} {request.path} 200')
    return jsonify(memory = memory), 200
