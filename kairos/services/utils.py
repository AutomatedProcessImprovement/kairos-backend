from dateutil import parser
from datetime import timedelta
import zipfile

import kairos.models.cases_model as cases_db
import kairos.models.event_logs_model as event_logs_db

EVALUATION_METHODS = {
            'EQUAL':lambda x,y: x == y,'NOT_EQUAL':lambda x,y: x!=y,'CONTAINS': lambda x,y: y in x,'NOT_CONTAINS':lambda x,y: y not in x,
            'GREATER_THAN':lambda x,y: x > y,'LESS_THAN':lambda x,y: x < y,'GREATER_THAN_OR_EQUAL':lambda x,y: x >= y,'LESS_THAN_OR_EQUAL':lambda x,y: x <= y,
            'IS_TRUE':lambda x,y: x == True,'IS_FALSE':lambda x,y: x == False,
            'LATER_THAN': lambda x,y: x > y,'EARLIER_THAN': lambda x,y: x < y,'LATER_THAN_OR_EQUAL': lambda x,y: x >= y,'EARLIER_THAN_OR_EQUAL': lambda x,y: x <= y,
            }

def expect(input, expectedType, field):
    if isinstance(input, expectedType):
        return input
    raise AssertionError("Invalid input for type", field)

def is_allowed_file(file):
    extension = file.filename.rsplit('.', 1)[1].lower()
    if extension == 'zip':
        zip = zipfile.ZipFile(file).filelist
        if zip:
            filename = zip[0].filename
            extension = filename.rsplit('.', 1)[1].lower()
    result = extension in ['xes','csv']
    return result

def validate_timestamp(data,columns_definition):
    timeTypes = ['TIMESTAMP','START_TIMESTAMP','END_TIMESTAMP','DATETIME']

    if columns_definition.get(data['column']) in timeTypes:
        data['value'] = parser.parse(data['value']).strftime('%Y-%m-%dT%H:%M:%SZ')

    return data['value']

def record_event(event_data,event_id,project_id):
    print('Recording event...')
    try:
        log = event_logs_db.get_event_log_by_project_id(project_id)
    except Exception as e:
        print(str(e))
        return
    event_log_id = log.get('_id')
    columns_definition = log.get("columns_definition")
    case_attributes_definition = log.get('case_attributes')

    case_id = 0
    activity = {'event_id': event_id}
    case_attributes = {}

    for k,v in event_data.get('data').items():
        attr = columns_definition.get(k)
        v = parse_value(k,v)

        if attr == 'CASE_ID':
            case_id = v
        elif attr == 'ACTIVITY':
            activity['ACTIVITY'] = v
        elif attr in ['TIMESTAMP','START_TIMESTAMP']:
            activity['TIMESTAMP'] = v
        elif k in case_attributes_definition:
            case_attributes[k] = v
        else:
            activity[k] = v

    prescriptions = event_data.get("prescriptions")
    prescriptions_with_output = [prescriptions[p] for p in prescriptions if prescriptions[p]["output"]]
    case_completed = event_data.get('case_completed')

    old_case = cases_db.get_case_by_log_id(case_id,event_log_id)
    
    if not old_case:
        _id = cases_db.save_case(case_id,event_log_id,case_completed,activity,prescriptions_with_output,case_attributes).inserted_id
        print(f'saved case: {_id}')
    else: 
        # try:
        #     update_case_prescriptions(case_id,activity['ACTIVITY'])
        # except Exception as e:
        #     print(f'Failed to update case prescriptions: {e}')

        cases_db.update_case(case_id,case_completed,activity,prescriptions_with_output)
        print(f'updated case: {case_id}')

    case_performance = {}
    try:
        case_performance = calculate_case_performance(case_id,log.get('positive_outcome'),columns_definition)
    except Exception as e:
        print(f'Failed to calculate case perfrmance: {e}')

    cases_db.update_case_performance(case_id,case_performance)
    print(f'updated case performance: {case_id}')

def update_case_prescriptions(case_id,new_activity):
    my_case = cases_db.get_case(case_id)

    previous_event_id = my_case['activities'][-1]['event_id']
    cases_db.update_case_prescriptions(case_id,previous_event_id,new_activity)

    print('updated case prescriptions')

def calculate_case_performance(case_id,positive_outcome, columns_definition):
    print('calculating case performance...')
    my_case = cases_db.get_case(case_id)
    
    column = positive_outcome['column']
    value = positive_outcome['value']
    operator = positive_outcome['operator']

    last_activity = my_case['activities'][-1]
    start = my_case['activities'][0]['TIMESTAMP']
    end = last_activity['TIMESTAMP']

    column_type = columns_definition.get(column)

    if column_type == None:
        if column == 'DURATION':
            duration = value.split(' ')
            value = int(duration[0])
            actual_value = calculate_duration(start,end,duration[1])

        else:
            raise Exception(f'Unsupported column: {column}')
    else:
        if column_type == 'ACTIVITY':
            column = 'ACTIVITY'
        elif column_type in ['TIMESTAMP','START_TIMESTAMP']:
            column = 'TIMESTAMP'
        actual_value = my_case.get('case_attributes').get(column) if not last_activity.get(column) else last_activity.get(column)
    
    if actual_value == None:
        print(f'something went wrong, actual value: {actual_value},column: {column}, outcome: {outcome}')
        raise Exception('something went wrong')
    
    value = parse_value(column_type, value)
    actual_value = parse_value(column_type,actual_value)

    outcome = EVALUATION_METHODS.get(operator)(actual_value,value)

    if column == 'DURATION': 
        actual_value = calculate_duration_without_units(start,end)

    case_performance = {
            'column': column,
            'value': actual_value,
            'outcome': outcome
            }
    print(f'case performance: {case_performance}')

    return case_performance

def calculate_duration(start,end,unit):
    time_units = {
        # 'months': 'months', # TODO timedelta does not support months
        # 'month': 'months',
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

    # print(f'start time: {start_time}, end time: {end_time}, duration: {duration}')
    return duration

def calculate_duration_without_units(start,end):
    start_time = parser.parse(start)
    end_time = parser.parse(end)

    duration = int((end_time - start_time).total_seconds())
    print(duration)
    if duration >= 604800: 
        measure = 'weeks'
        duration /= 604800
    elif duration >= 86400: 
        measure = 'days' 
        duration /= 86400
    elif duration >= 3600: 
        measure = 'hours'
        duration /= 3600
    elif duration >= 60:
         measure = 'minutes'
         duration /= 60
    else: measure = 'seconds'
    duration = round(duration)
    result = f'{duration} {measure}'
    return result

def parse_value(column_type,value):
    if column_type in ['TEXT','RESOURCE','ACTIVITY']:
        value = str(value)
    elif column_type in ['COST','DURATION','NUMBER']:
        value = float(value)

    elif column_type in ['DATEITME','TIMESTAMP','START_TIMESTAMP','END_TIMESTAMP']:
        value = parser.parse(value, ignoretz=True)

    return value