from dateutil import parser
from datetime import timedelta,datetime
from pymongo.errors import DuplicateKeyError
from collections import Counter
from flask import current_app

import copy
import math
import random
import string
import pytz

from kairos.enums.column_type import Column_type as COLUMN_TYPE

import kairos.models.cases_model as cases_db
import kairos.models.event_logs_model as event_logs_db

EVALUATION_METHODS = {
            'EQUAL':lambda x,y: x == y,'NOT_EQUAL':lambda x,y: x!=y,'CONTAINS': lambda x,y: y in x,'NOT_CONTAINS':lambda x,y: y not in x,
            'GREATER_THAN':lambda x,y: x > y,'LESS_THAN':lambda x,y: x < y,'GREATER_THAN_OR_EQUAL':lambda x,y: x >= y,'LESS_THAN_OR_EQUAL':lambda x,y: x <= y,
            'IS_TRUE':lambda x,y: x == True,'IS_FALSE':lambda x,y: x == False,
            'LATER_THAN': lambda x,y: x > y,'EARLIER_THAN': lambda x,y: x < y,'LATER_THAN_OR_EQUAL': lambda x,y: x >= y,'EARLIER_THAN_OR_EQUAL': lambda x,y: x <= y,
            }

def is_allowed_file(file):
    try:
        extension = file.filename.rsplit('.', 1)[1].lower()
    except Exception as e:
        print(str(e))
        return False
    return extension in ['xes','csv','zip']

def format_file(name,file):
    file.stream.seek(0)
    formatted = (name, (file.filename, file.stream, file.content_type))
    return formatted
    
def validate_and_reverse_columns_definition(columns_definition):
    if not columns_definition:
        raise Exception('Columns definition cannot be null.')
    
    rev_dict = {}
 
    for key, value in columns_definition.items():
        rev_dict.setdefault(value, set()).add(key)
        
    count_column_types = Counter(columns_definition.values())
    duplicates = [k for k, v in count_column_types.items() if v > 1] 

    if COLUMN_TYPE.ACTIVITY in duplicates:
        raise Exception('The log can include only one ACTIVITY column.')
       
    columns_definition_reverse = {v: k for k, v in columns_definition.items() if v in [COLUMN_TYPE.CASE_ID,COLUMN_TYPE.ACTIVITY,COLUMN_TYPE.TIMESTAMP,COLUMN_TYPE.START_TIMESTAMP,COLUMN_TYPE.END_TIMESTAMP,COLUMN_TYPE.RESOURCE]}
    
    if not columns_definition_reverse.get(COLUMN_TYPE.CASE_ID):
        raise Exception('The log must include a CASE_ID column.')
    
    if not columns_definition_reverse.get(COLUMN_TYPE.ACTIVITY):
        raise Exception('The log must include an ACTIVITY column.')
    
    if not columns_definition_reverse.get(COLUMN_TYPE.TIMESTAMP) and not (columns_definition_reverse.get(COLUMN_TYPE.START_TIMESTAMP) and columns_definition_reverse.get(COLUMN_TYPE.END_TIMESTAMP)):
        raise Exception('The log must include a TIMESTAMP column or START_TIMESTAMP and END_TIMESTAMP columns.')
    
    if columns_definition_reverse.get(COLUMN_TYPE.TIMESTAMP):
        columns_definition_reverse[COLUMN_TYPE.END_TIMESTAMP] = columns_definition_reverse.get(COLUMN_TYPE.TIMESTAMP)
        columns_definition_reverse[COLUMN_TYPE.START_TIMESTAMP] = columns_definition_reverse.get(COLUMN_TYPE.TIMESTAMP)
        columns_definition_reverse.pop(COLUMN_TYPE.TIMESTAMP)
    
    return columns_definition_reverse

def format_positive_outcome(positive_outcome):
    prcore_outcome = copy.deepcopy(positive_outcome)
    if prcore_outcome.get('unit'):
        prcore_outcome['value'] = f'{prcore_outcome.get("value")} {prcore_outcome.get("unit")}'
        prcore_outcome.pop('unit')
    return prcore_outcome

def record_event(event_data,event_id,project_id):
    try:
        log = event_logs_db.get_event_log_by_project_id(project_id)
    except Exception as e:
        print(str(e))
        return 
    event_log_id = log.get('_id')
    columns_definition = log.get("columns_definition")
    columns_definition_reverse = log.get('columns_definition_reverse')
    case_attributes_definition = log.get('case_attributes')

    case_id = 0
    activity = {'event_id': event_id}
    case_attributes = {}

    for column,value in event_data.get('data').items():
        column_type = columns_definition.get(column)
        value = parse_value(column_type,value)
        
        if column_type == 'CASE_ID':
            case_id = value
        elif column in case_attributes_definition:
            case_attributes[column] = value
        else:
            activity[column] = value

    prescriptions = event_data.get("prescriptions")
    prescriptions_with_output = [prescriptions[p] for p in prescriptions if prescriptions[p]["output"]]
    case_completed = event_data.get('case_completed')
    if case_completed:
        prescriptions_with_output = []
    activity['prescriptions'] = prescriptions_with_output

    try:
        old_case = cases_db.get_case(case_id)
    except Exception:
        old_case = None
    
    if not old_case:
        _id = cases_db.save_case(case_id,event_log_id,case_completed,[activity],case_attributes).inserted_id
    else: 
        try:
            update_case_prescriptions(old_case,activity,columns_definition_reverse.get(COLUMN_TYPE.ACTIVITY))
        except Exception as e:
            print(f'Failed to update case {case_id} prescriptions: {e}')
        timestamp_column = columns_definition_reverse.get(COLUMN_TYPE.START_TIMESTAMP)
        cases_db.update_case(case_id,case_completed,activity,str(timestamp_column))

    case_performance = {}
    try:
        case_performance = calculate_case_performance(case_id,log.get('positive_outcome'),columns_definition, columns_definition_reverse)
    except Exception as e:
        print(f'Failed to calculate case {case_id} perfrmance: {e}')

    try:
        cases_db.update_case_performance(case_id,case_performance)
    except Exception as e:
        print(f'Failed to update case {case_id} perfrmance: {e}')

    current_app.logger.info(f'''STREAMING RESULT: 
                            event_log_id: {event_log_id},
                            project_id: {project_id},
                            case_id: {case_id},
                            prescriptions: {prescriptions}''')
    return case_id


def update_case_prescriptions(my_case,new_activity,activity_column):    
    new_activities = my_case.get('activities')
    last_activity = new_activities[-1]

    for p in last_activity.get('prescriptions'):
        status = 'discarded'
        if p.get('type') == 'NEXT_ACTIVITY' and p.get('output') == new_activity.get(activity_column):
            status = 'accepted'
        elif p.get('type') == 'TREATMENT_EFFECT':
            treatment =  p.get('output').get('treatment')[0][0]
            treatment_column = new_activity.get(treatment.get('column'))
            if treatment_column:
                if EVALUATION_METHODS.get(treatment.get('operator'))(treatment_column,treatment.get('value')):
                    status = 'accepted'
        p['status'] = status
    cases_db.update_case_prescriptions(my_case.get('_id'),new_activities)

def calculate_case_performance(case_id,positive_outcome, columns_definition, columns_definition_reverse):
    my_case = cases_db.get_case(case_id)
    
    column = positive_outcome['column']
    value = positive_outcome['value']
    operator = positive_outcome['operator']

    last_activity = my_case['activities'][-1]
    start = my_case['activities'][0][columns_definition_reverse.get(COLUMN_TYPE.START_TIMESTAMP)]
    end = last_activity.get(columns_definition_reverse.get(COLUMN_TYPE.END_TIMESTAMP))

    column_type = columns_definition.get(column)

    if column_type == None:
        if column == COLUMN_TYPE.DURATION:
            column_type = COLUMN_TYPE.DURATION
            unit = positive_outcome.get('unit')
            actual_value = calculate_duration(start,end,unit)
        else:
            raise Exception(f'Unsupported column: {column}')
    else:
        actual_value = my_case.get('case_attributes').get(column) if not last_activity.get(column) else last_activity.get(column)
    
    if actual_value == None:
        print(f'something went wrong, actual value: {actual_value},column: {column}')
        raise Exception('something went wrong while calculating case performance.')

    # value = parse_value(column_type, value)
    # actual_value = parse_value(column_type,actual_value)

    outcome = EVALUATION_METHODS.get(operator)(actual_value,value)

    unit = None
    if column == 'DURATION': 
        actual_value,unit = calculate_duration_without_units(start,end)

    case_performance = {
            'column': column,
            'value': actual_value,
            'outcome': outcome,
            'unit':unit
            }
    return case_performance

def calculate_duration(start,end,unit):
    time_units = {
        'weeks': 'weeks',
        'week': 'weeks',
        'days': 'days',
        'day': 'days',
        'hours': 'hours',
        'hour': 'hours',
        'minutes': 'minutes',
        'minute': 'minutes',
        'seconds':'seconds',
        'second':'seconds'
    }
    if isinstance(start, str) and isinstance(end, str):
        start = parser.parse(start)
        end = parser.parse(end)
    
    if unit not in time_units:
        raise Exception(f'Invalid time unit for duration: {unit}')
    
    duration = (end - start) // timedelta(**{time_units[unit]: 1})

    return duration

def calculate_duration_without_units(start,end):
    if isinstance(start, str) and isinstance(end, str):
        start = parser.parse(start)
        end = parser.parse(end)

    duration = int((end - start).total_seconds())
    if duration >= 604800 and (duration % 604800) < 86400:
        unit = 'weeks'
        duration /= 604800
    elif duration >= 86400: 
        unit = 'days' 
        duration /= 86400
    elif duration >= 3600: 
        unit = 'hours'
        duration /= 3600
    elif duration >= 60:
         unit = 'minutes'
         duration /= 60
    else: unit = 'seconds'
    duration = math.floor(duration)
    return duration,unit

def parse_value(column_type,value):
    value = str(value)
    if column_type in [COLUMN_TYPE.COST,COLUMN_TYPE.DURATION,COLUMN_TYPE.NUMBER]:
        try:
            value = float(value)
            if math.isnan(value): value = 'nan'
        except ValueError:
            value = 'nan'
    elif column_type in [COLUMN_TYPE.DATETIME,COLUMN_TYPE.TIMESTAMP,COLUMN_TYPE.START_TIMESTAMP,COLUMN_TYPE.END_TIMESTAMP]:
        try:
            value = parser.parse(value, ignoretz=True)
        except Exception:
            current_app.logger.error("Could not parse datetime object")
            value = str(value)
    elif column_type == COLUMN_TYPE.BOOLEAN:
        value = value in ['True','true',True]

    return value

def record_results(project_id,result):
    if result.get('cases') == None:
        return
    
    try:
        log = event_logs_db.get_event_log_by_project_id(project_id)
    except Exception as e:
        print(str(e))
        return
    
    event_log_id = log.get('_id')
    columns = result.get('columns')
    columns_definition = log.get("columns_definition")
    columns_definition_reverse = log.get('columns_definition_reverse')
    case_attributes_definition = log.get('case_attributes')
    suffix = generate_suffix()

    for case_id, case_body in result.get('cases',{}).items():
        events = case_body.get('events',[])
        prescriptions = case_body.get('prescriptions',[])
        prescriptions_with_output = [p for p in prescriptions if p["output"]]
        activities = []
        case_attributes = {}

        for i in range(len(events)):
            event_data = events[i]
            event_data = dict(zip(columns, event_data))
            activity = {'event_id': i}

            for column,value in event_data.items():
                column_type = columns_definition.get(column)
                value = parse_value(column_type,value)
                
                if column_type == 'CASE_ID':
                    continue
                elif column in case_attributes_definition:
                    case_attributes[column] = value
                else:
                    activity[column] = value
            if i == (len(events) - 1):
                activity['prescriptions'] = prescriptions_with_output
            
            activities.append(activity)
        case_completed = False

        while True:
            try:
                _id = cases_db.save_case(suffix + str(case_id),event_log_id,case_completed,activities,case_attributes).inserted_id
                break
            except DuplicateKeyError:
                suffix = generate_suffix()
        
        # print(f'saved case: {_id}')

        case_performance = {}
        try:
            case_performance = calculate_case_performance(_id,log.get('positive_outcome'),columns_definition, columns_definition_reverse)
        except Exception as e:
            print(f'Failed to calculate case {case_id} perfrmance: {e}')

        try:
            cases_db.update_case_performance(_id,case_performance)
        except Exception as e:
            print(f'Failed to update case {case_id} perfrmance: {e}')
        
    event_logs_db.update_event_log(event_log_id,{'got_results': True})  

def generate_suffix():
    rand = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    return rand + '-'