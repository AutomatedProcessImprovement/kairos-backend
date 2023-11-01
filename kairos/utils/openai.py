import openai
import os

from dotenv import load_dotenv
from flask import current_app

import kairos.models.messages_model as messages_db

load_dotenv()

openai.api_key = os.environ.get('OPENAI_API_KEY')

SYSTEM_MESSAGE = '''
    You are a smart assistant to a process analyst. Your job is to provide relevant information to any questions concerning a completed case of a business process. 
    The case information is provided as context in messages.
    The business processes may vary, but its cases will always include: case id, timestamp, activities and event log id is it associated with. 
    The activities are the events that have taken place within the process instance. Each event will have a list of prescriptions associated with it. 
    A prescription signifies a recommended course of action in the process to mitigate a negative outcome or improve a KPI. The available prescription types are as follows:

    NEXT_ACTIVITY : This is an algorithm which predicts the next activity of a case in a business process as output.

    ALARM: This is an algorithm that calculates the probability of a negative outcome which is defined as output,
    
    TREATMENT_EFFECT: This is an algorithm that produces an output defined as following. The output is an object with the following fields: proba_if_treated: The probability of a positive outcome if the case is treated. proba_if_untreated: The probability of a positive outcome if the case is not treated. cate: The Conditional Average Treatment Effect (CATE) score of the case. treatment: The treatment definition of the case. This is directly from the user’s previously inputted treatment definition.

    '''

def ask_ai(content,event_log_id=None,case_id=None):
    messages = []    
    if case_id:
        messages = messages_db.get_context_by_case_id(case_id=case_id)
    elif event_log_id:
        messages = messages_db.get_context_by_log_id(event_log_id=event_log_id)
    else:
        messages = messages_db.get_context()

    messages.insert(0,{
        'role':'system',
        'content': SYSTEM_MESSAGE,
    })

    new_message = {
        'role':'user',
        'content': content
    }
    messages.append(new_message)

    try:
        chat = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages,)
    except Exception as e:
        current_app.logger.error(f'Error in openAI call - {e}')
        return None
    
    reply_content = chat.get('choices')[0].get('message').get('content')

    messages_db.save_message(role='user',content=content,event_log_id=event_log_id,case_id=case_id)
    messages_db.save_message(role='assistant',content=reply_content,event_log_id=event_log_id,case_id=case_id)

    return reply_content

def save_context(context,event_log_id=None,case_id=None):
    messages_db.save_message(role='user',content=context,context=True,event_log_id=event_log_id,case_id=case_id)