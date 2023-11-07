from dateutil import parser
from datetime import timedelta
from collections import Counter
from flask import current_app

import copy
import math
import random
import string

from kairos.enums.column_type import Column_type as COLUMN_TYPE

import kairos.models.cases_model as cases_db

EVALUATION_METHODS = {
            'EQUAL':lambda x,y: x == y,'NOT_EQUAL':lambda x,y: x!=y,'CONTAINS': lambda x,y: y in x,'NOT_CONTAINS':lambda x,y: y not in x,
            'GREATER_THAN':lambda x,y: x > y,'LESS_THAN':lambda x,y: x < y,'GREATER_THAN_OR_EQUAL':lambda x,y: x >= y,'LESS_THAN_OR_EQUAL':lambda x,y: x <= y,
            'IS_TRUE':lambda x,y: x == True,'IS_FALSE':lambda x,y: x == False,
            'LATER_THAN': lambda x,y: x > y,'EARLIER_THAN': lambda x,y: x < y,'LATER_THAN_OR_EQUAL': lambda x,y: x >= y,'EARLIER_THAN_OR_EQUAL': lambda x,y: x <= y,
            }

THRESHOLD_FACTOR = 1

def is_allowed_file(file):
    try:
        extension = file.filename.rsplit('.', 1)[1].lower()
    except Exception as e:
        current_app.logger.error(f'Error in is_allowed_file: {str(e)}')
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
    for group in prcore_outcome:
        for item in group:
            if item.get('unit'):
                item['value'] = f'{item.get("value")} {item.get("unit")}'
                item.pop('unit')
    return prcore_outcome

def format_additional_info(additional_info):
    if not additional_info: return None
    prcore_additional_info = copy.deepcopy(additional_info)
    
    treatment_duration = prcore_additional_info['plugin_causallift_resource_allocation']['treatment_duration']
    prcore_additional_info['plugin_causallift_resource_allocation']['treatment_duration'] = f'{treatment_duration.get("value")}{treatment_duration.get("unit")}'
    prcore_additional_info['plugin-causallift-resource-allocation'] = prcore_additional_info.pop('plugin_causallift_resource_allocation')
    return prcore_additional_info

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
    
    if type(positive_outcome) is dict:
        positive_outcome = [[positive_outcome]]

    case_performance = []

    for i in range(len(positive_outcome)):
        case_performance.append([])
        for j in range(len(positive_outcome[i])):
            positive_outcome_item = positive_outcome[i][j]

            column = positive_outcome_item['column']
            value = positive_outcome_item['value']
            operator = positive_outcome_item['operator']
            unit = positive_outcome_item.get('unit')

            last_activity = my_case['activities'][-1]
            start = my_case['activities'][0][columns_definition_reverse.get(COLUMN_TYPE.START_TIMESTAMP)]
            end = last_activity.get(columns_definition_reverse.get(COLUMN_TYPE.END_TIMESTAMP))

            column_type = columns_definition.get(column)

            if column_type == None:
                if column == COLUMN_TYPE.DURATION:
                    column_type = COLUMN_TYPE.DURATION
                    actual_value = calculate_duration(start,end,unit)
                else:
                    raise Exception(f'Unsupported column: {column}')
            else:
                actual_value = my_case.get('case_attributes').get(column) if not last_activity.get(column) else last_activity.get(column)
            
            if actual_value == None:
                current_app.logger.error(f'something went wrong, actual value: {actual_value},column: {column}')
                raise Exception('something went wrong while calculating case performance.')

            value = parse_value(column_type, value)
            actual_value = parse_value(column_type,actual_value)

            outcome = EVALUATION_METHODS.get(operator)(actual_value,value)

            unit = None
            if column == 'DURATION': 
                actual_value,unit = calculate_duration_without_units(start,end)

            case_performance[i].append({
                    'column': column,
                    'value': actual_value,
                    'outcome': outcome,
                    'unit':unit
                    })
            
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
    start_time = parser.parse(start)
    end_time = parser.parse(end)
    
    if unit not in time_units:
        raise Exception(f'Invalid time unit for duration: {unit}')
    
    duration = (end_time - start_time) // timedelta(**{time_units[unit]: 1})

    return duration

def calculate_duration_without_units(start,end):
    start_time = parser.parse(start)
    end_time = parser.parse(end)

    duration = int((end_time - start_time).total_seconds())
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
            value = parser.parse(value, ignoretz=True).strftime('%Y-%m-%d %H:%M:%SZ')
        except Exception:
            value = str(value)
    elif column_type == COLUMN_TYPE.BOOLEAN:
        value = value in ['True','true',True]

    return value


def generate_suffix():
    rand = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    return rand + '-'

def categorize_cate(event_log_id,new_prescription):
    aggregate = cases_db.get_treatment_mean_and_std(event_log_id)
    if not aggregate: return None

    _,mean_cate,std_dev_cate = aggregate[0].values()
    
    current_cate = None

    if mean_cate and std_dev_cate:
        low_threshold = mean_cate - THRESHOLD_FACTOR * std_dev_cate
        high_threshold = mean_cate + THRESHOLD_FACTOR * std_dev_cate

        cate_value = new_prescription.get('output', {}).get('cate', None)

        if cate_value < low_threshold:
            current_cate = "low"
        elif cate_value > high_threshold:
            current_cate = "high"
        else:
            current_cate = "medium"

    return current_cate
