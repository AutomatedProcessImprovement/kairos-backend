from pymongo.errors import DuplicateKeyError

from kairos.enums.column_type import Column_type as COLUMN_TYPE

import kairos.models.cases_model as cases_db
import kairos.models.event_logs_model as event_logs_db

from kairos.utils import parse_value, generate_suffix, calculate_case_performance, update_case_prescriptions

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
    prescriptions_with_output = [prescriptions[p] for p in prescriptions if prescriptions[p].get('output')]

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

        cases_db.update_case(case_id,case_completed,activity)

    case_performance = {}
    try:
        case_performance = calculate_case_performance(case_id,log.get('positive_outcome'),columns_definition, columns_definition_reverse)
    except Exception as e:
        print(f'Failed to calculate case {case_id} perfrmance: {e}')

    try:
        cases_db.update_case_performance(case_id,case_performance)
    except Exception as e:
        print(f'Failed to update case {case_id} perfrmance: {e}')

    return case_id

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