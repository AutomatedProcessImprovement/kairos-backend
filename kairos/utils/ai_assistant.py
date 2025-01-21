from openai import OpenAI
from kairos.models.db import query_db, find_similar_cases
from kairos.enums.assistant_data import ASSISTANT_DATA
from flask import current_app
from json import JSONDecodeError

import kairos.models.cases_model as cases_db
import kairos.models.event_logs_model as event_logs_db

import json
import time
import re

client = OpenAI(default_headers={"OpenAI-Beta": "assistants=v2"})

def ask_ai(case_id, event_log_id, question):
    thread_id = get_case_thread_id(case_id)
    case_instance = cases_db.get_case_structure(case_id)
    
    event_log_instance = event_logs_db.get_event_log_structure(event_log_id)
    
    # Create a user message
    current_app.logger.info(f' Thread: {thread_id}')
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=question
    )
    current_app.logger.info(f'Added message to thread')

    instructions = ASSISTANT_DATA.instructions(
        event_logs_db_structure=event_log_instance,
        cases_db_structure=case_instance,
        event_log_id=event_log_id,
        case_id=case_id
    )

    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=current_app.config.get('OPENAI_ASSISTANT_ID'),
        instructions=instructions
    )
    run_id = run.id
    current_app.logger.info(f' Ran thread {run_id}')
    rate_limit_exceeded_iterations = 0
    while True:
        # Retrieve run
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        current_app.logger.info(f'Run status: {run.status}')

        if run.status == "completed":
            break
        elif run.status == "requires_action":
            current_app.logger.info(f' Run requires action')

            if run.required_action and run.required_action.type == "submit_tool_outputs":
                tool_calls = run.required_action.submit_tool_outputs.tool_calls
                if tool_calls:
                    available_functions = {
                        "query_db" : query_db,
                        "find_similar_cases" : find_similar_cases
                    }
                    tool_outputs = []
                    for tool_call in tool_calls:

                        tool_call_id = tool_call.id
                        function_name = tool_call.function.name
                        function_to_call = available_functions[function_name]

                        function_args = convert_to_json(tool_call.function.arguments)
                        
                        if function_name == "query_db":

                            collection = function_args.get('collection')

                            if collection == None:
                                current_app.logger.error('Collection field was null. Defaulting to base value.')
                                collection = 'cases'

                            aggregate = function_args.get('aggregate')

                            if aggregate == None:
                                current_app.logger.error(f'Aggregate field was null. Defaulting to base query. Aggregate field: {aggregate}')
                                aggregate = [{"$match": {"_id": case_id}}]

                            current_app.logger.info(f'Running function {function_to_call} with args {collection,aggregate}')
                            
                            try:
                                function_response = function_to_call(
                                    collection=collection,
                                    aggregate=aggregate,
                                )
                            except Exception as e:
                                current_app.logger.error(f"An error occured while calling function with AI generated arguments, cancelling run {run_id}. - {str(e)}")
                                client.beta.threads.runs.cancel(
                                    thread_id=thread_id,
                                    run_id=run_id,
                                )
                                raise Exception("An error occured while retrieving AI assistant response. Please try again.")
                                
                        else:
                            case_id_arg = function_args.get('case_id') or case_id
                            current_app.logger.info(f'Running function {function_to_call} with args {case_id}')

                            function_response = function_to_call(case_id=case_id_arg)

                        function_response = str(list(function_response))
                        current_app.logger.info(f'Function respone: {function_response}')
                        
                        tool_outputs.append({
                            "tool_call_id" : tool_call_id,
                            "output" : function_response
                        })
                    run = client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread_id,
                        run_id=run_id,
                        tool_outputs=tool_outputs
                    )
                    run_id = run.id
                    current_app.logger.info(f'Submitted tool outputs')
            time.sleep(4)
            continue
                 
        elif run.status in ["cancelled","failed","expired"]:
            error_message = run.last_error.message or f"The run has {run.status}."
            current_app.logger.error(error_message)
            if run.last_error.code == "rate_limit_exceeded" and rate_limit_exceeded_iterations < 1:

                rate_limit_exceeded_iterations += 1
                number = 10
                match = re.search(r"Please try again in (\d+\.\d+)s", error_message)
                if match:
                    number_str = match.group(1)
                    number = float(number_str)
                
                time.sleep(number + 10.0)
            else:
                if rate_limit_exceeded_iterations > 0:
                    error_message = f"Rate limit reached. Please try again in {number} seconds."
                raise Exception(error_message)
        else:
            time.sleep(4)
    
    messages = client.beta.threads.messages.list(thread_id,limit=50)
    if len(messages.data) > 0:
        last_message = messages.data[0]
        return format_message(last_message)

def get_messages_by_case_id(case_id,last_message=None):
    thread_id = get_case_thread_id(case_id)
    
    thread_messages = thread_messages = client.beta.threads.messages.list(thread_id,limit=50,after=last_message,order='asc')
    formatted_messages = [format_message(message) for message in thread_messages]

    return list(formatted_messages)

def get_case_thread_id(case_id):
    case_instance = cases_db.get_case(case_id)
    thread_id = case_instance.get('thread_id')
    
    if not thread_id:
        thread_id = client.beta.threads.create().id
        cases_db.update_case_thread_id(case_id,thread_id)

    return thread_id

def delete_case_thread_id(case_id):
    case_instance = cases_db.get_case(case_id)
    thread_id = case_instance.get('thread_id')
    
    if thread_id != None:
        client.beta.threads.delete(thread_id=thread_id)
        cases_db.update_case_thread_id(case_id,None)

def format_message(message):
    formatted_message = {
        "id": message.id,
        "role": message.role,
        "content": message.content[0].text.value
    }

def modify_assistant():
    client.beta.assistants.update(
        assistant_id=current_app.config.get('OPENAI_ASSISTANT_ID'),
        instructions=ASSISTANT_DATA.instructions
    )

def convert_to_json(json_string):
    if not json_string:
        return {}

    json_string = json_string.replace('True', 'true').replace('False', 'false').replace('None', 'null')

    try:
        return json.loads(json_string)
    except JSONDecodeError as e:
        current_app.logger.error(f"JSON decoding error: {str(e)}")
        return {}