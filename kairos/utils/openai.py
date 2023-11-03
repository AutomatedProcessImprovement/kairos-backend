import openai
import os
import tiktoken

from dotenv import load_dotenv
from flask import current_app

import kairos.models.messages_model as messages_db
import kairos.models.cases_model as cases_db

load_dotenv()

openai.api_key = os.environ.get('OPENAI_API_KEY')

SYSTEM_MESSAGE = '''
    You are a smart assistant to a process analyst. Your job is to provide relevant information to any questions concerning a case of a business process using markdown format.
    The case information is provided as context in messages.
    The cases will always include: case id, timestamp, activities and event log id is it associated with. 
    Each activity has a list of prescriptions, which signify a recommended course of action in the process to mitigate a negative outcome or improve a KPI. The available prescriptive algorithms are as follows:
    NEXT_ACTIVITY: predicts the next activity of a case in a business process as output.
    ALARM: Algorithm calculates the probability of a negative outcome which is defined as output,
    TREATMENT_EFFECT: produces an output as object with the following fields: proba_if_treated: The probability of a positive outcome if the case is treated. proba_if_untreated: The probability of a positive outcome if the case is not treated. cate: The Conditional Average Treatment Effect (CATE) score of the case. treatment: The treatment definition of the case: the next best course of action defined by the user.
    '''

MODEL = 'gpt-3.5-turbo-0613'
RESPONSE_TOKENS = 100
PROMPT_TOKENS = 4000 - RESPONSE_TOKENS

def ask_ai(content,event_log_id=None,case_id=None):
    if not case_id:
        current_app.logger.error('Case id cannot be null.')
        raise Exception('Error in ask openai call: Case id cannot be null.')

    case_context = cases_db.get_case(case_id=case_id)

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
    
    messages.insert(0,{
        'role':'user',
        'content': f'Case context: {case_context}',
    })

    request_tokens = num_tokens_from_messages(messages, MODEL)

    if request_tokens > PROMPT_TOKENS:
        chat_summary = summarize_messages(messages)
        messages = [{
            'role': 'user',
            'content': chat_summary
        }]

    new_message = {
        'role':'user',
        'content': content
    }
    messages.append(new_message)

    try:
        chat = openai.ChatCompletion.create(
            model=MODEL, 
            messages=messages,
            max_tokens=RESPONSE_TOKENS,
            temperature=0.2
        )
    except Exception as e:
        current_app.logger.error(f'Error in openAI call - {e}')
        return None
    
    reply_content = chat.get('choices')[0].get('message').get('content')

    messages_db.save_message(role='user',content=content,event_log_id=event_log_id,case_id=case_id)
    messages_db.save_message(role='assistant',content=reply_content,event_log_id=event_log_id,case_id=case_id)

    return reply_content

def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613"):
    """Return the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    if model in {
        "gpt-3.5-turbo-0613",
        "gpt-3.5-turbo-16k-0613",
        "gpt-4-0314",
        "gpt-4-32k-0314",
        "gpt-4-0613",
        "gpt-4-32k-0613",
        }:
        tokens_per_message = 3
        tokens_per_name = 1
    elif model == "gpt-3.5-turbo-0301":
        tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif "gpt-3.5-turbo" in model:
        print("Warning: gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0613.")
        return num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613")
    elif "gpt-4" in model:
        print("Warning: gpt-4 may update over time. Returning num tokens assuming gpt-4-0613.")
        return num_tokens_from_messages(messages, model="gpt-4-0613")
    else:
        raise NotImplementedError(
            f"""num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens."""
        )
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens

def summarize_messages(messages):
    chat = openai.ChatCompletion.create(
        model=MODEL, 
        messages=messages,
        max_tokens=2000,
    )

    messages.append({
        'role':'user',
        'content': 'Summarize the previous messages. Make sure to include case information.'
    })

    reply = chat.get('choices')[0].get('message').get('content')
    return reply