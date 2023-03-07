from dateutil import parser
from datetime import timedelta

from kairos.models.cases_model import ( get_case_by_project_id, get_case, save_case, update_case, update_case_prescriptions, update_case_performance)
from kairos.models.event_logs_model import get_event_log_by_project_id

def record_event(event_data,event_id,project_id):
    print('Recording event...')
    try:
        log = get_event_log_by_project_id(project_id)
    except Exception as e:
        print(str(e))
        return
    columns_definition = log.get("columns_definition")
    case_attributes_definition = log.get('case_attributes')

    case_id = 0
    activity = {'event_id': event_id}
    case_attributes = {}

    for k,v in event_data.get('data').items():
        attr = columns_definition.get(k)
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

    try:
        old_case = get_case_by_project_id(case_id,project_id)
    except Exception as e:
        return e
    
    if not old_case:
        _id = save_case(case_id,project_id,case_completed,activity,prescriptions_with_output,case_attributes).inserted_id
        print(f'case id: {case_id}, type of case id: {type(case_id)}')
        print(f'saved case: {_id}, type of id: {type(_id)}')
    else:
        new_event_id = old_case['activities'][-1]['event_id']
        print(new_event_id)
        update_case_prescriptions(case_id,new_event_id,activity['ACTIVITY'])
        print('updated case prescriptions')
        update_case(case_id,case_completed,activity,prescriptions_with_output)
        print(f'updated case: {case_id}')

    case_performance = {}
    try:
        case_performance = calculate_case_performance(case_id,log.get('positive_outcome'),columns_definition)
    except Exception as e:
        return e

    update_case_performance(case_id,case_performance)
    print(f'updated case performance')

def calculate_case_performance(case_id,positive_outcome, columns_definition):
    print('calculating case performance')
    try:
        my_case = get_case(case_id)
    except Exception as e:
        return e
    
    if not my_case:
        raise Exception(f'No case with id {case_id} found.')
    
    evaluation_methods = {
                'EQUAL':lambda x,y: x == y,'NOT_EQUAL':lambda x,y: x!=y,'CONTAINS': lambda x,y: y in x,'NOT_CONTAINS':lambda x,y: y not in x,
                'GREATER_THAN':lambda x,y: x > y,'LESS_THAN':lambda x,y: x < y,'GREATER_THAN_OR_EQUAL':lambda x,y: x >= y,'LESS_THAN_OR_EQUAL':lambda x,y: x <= y,
                'IS_TRUE':lambda x,y: x == True,'IS_FALSE':lambda x,y: x == False,
                'LATER_THAN': lambda x,y: x > y,'EARLIER_THAN': lambda x,y: x < y,'LATER_THAN_OR_EQUAL': lambda x,y: x >= y,'EARLIER_THAN_OR_EQUAL': lambda x,y: x <= y,
                }
    print(positive_outcome)
    column = positive_outcome['column']
    value = positive_outcome['value']
    operator = positive_outcome['operator']

    last_activity = my_case['activities'][-1]
    print(last_activity)
    
    if columns_definition[column] == 'ACTIVITY':
        column = 'ACTIVITY'
    elif columns_definition[column] in ['TIMESTAMP','START_TIMESTAMP']:
        column = 'TIMESTAMP'

    actual_value = last_activity.get(column) if last_activity.get(column) else my_case.get('case_attributes').get(column)
    print(f'actual value: {actual_value}')
    if not actual_value:
        if column == 'DURATION':
            duration = value.split(' ')
            value = duration[0]
            try:
                actual_value,unit = calculate_duration(my_case['activities'][0]['TIMESTAMP'],last_activity['TIMESTAMP'],duration[1])
            except Exception as e:
                return e
        else:
            raise Exception(f'Unsupported column type: {column}')

    outcome = evaluation_methods[operator](actual_value,value)
    if unit: actual_value = f'{actual_value} {unit}'
    print(f'outcome: {outcome}')

    return {
            'column': column,
            'value': actual_value,
            'outcome': outcome
            }

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
    try:
        start_time = parser.parse(start)
        end_time = parser.parse(end)
    except Exception as e:
        return e
    
    if unit not in time_units:
        raise Exception(f'Invalid time unit for duration: {unit}')
    
    duration = (end_time - start_time) // timedelta(**{time_units[unit]: 1})
    duration_unit = time_units[unit] if duration > 1 else time_units[unit][:-1]

    # print(f'start time: {start_time}, end time: {end_time}, duration: {duration}')
    return duration,duration_unit
