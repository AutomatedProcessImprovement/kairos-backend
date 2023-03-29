import kairos.models.cases_model as cases_db
import kairos.models.event_logs_model as event_logs_db
from kairos.services.signals import case_updated
from kairos.services import prcore_service

import json
import time

from flask_sse import sse

from flask import current_app, jsonify, stream_with_context,request

def stream_cases_by_log(event_log_id):
    def generate():
        def handle_event(sender,**kwargs):
            try:
                c = cases_db.get_case_by_log_idkwarg(kwargs['case_id'],event_log_id)
                if not c:
                    pass
            except Exception as e:
                yield 'event: error\ndata: {}\n\n'.format(str(e))
            yield 'event: user-updated\ndata: {}\n\n'.format(json.dumps(c))

        case_updated.connect(handle_event(),current_app._get_current_object())
        for _ in case_updated:
            pass

        case_updated.disconnect(handle_event)
    return current_app.response_class(stream_with_context(generate()),mimetype='text/event-stream')


def stream_project_status(event_log_id):
    try:
        log = event_logs_db.get_event_log(event_log_id)
    except Exception as e:
        return jsonify(error = str(e)), 400
    
    project_id = log.get('project_id')
    if project_id == None:
        return jsonify(status = 'NULL'),200
    
    old_status = ''

    while True:
        new_status = prcore_service.get_project_status(project_id)
        print(f'old: {old_status}, new: {new_status}')
        print(request.environ.get('HTTP_CONNECTION'))
        if old_status == new_status:
            time.sleep(4)
            continue
        old_status = new_status
        res = {"status": new_status}
        sse.publish(res,type='status changed')
        time.sleep(4)

    return "connection closed"

# def stream_project_status(event_log_id):
#     try:
#         log = event_logs_db.get_event_log(event_log_id)
#     except Exception as e:
#         return jsonify(error = str(e)), 400
    
#     project_id = log.get('project_id')
#     if project_id == None:
#         return jsonify(status = 'NULL'),200
    
#     old_status = ''

#     def generate():
#         nonlocal old_status
#         while True:
#             new_status = prcore_service.get_project_status(project_id)
#             print(f'old: {old_status}, new: {new_status}')
#             print(request.environ.get('HTTP_CONNECTION'))
#             if old_status == new_status:
#                 time.sleep(4)
#                 continue
#             old_status = new_status
#             res = {"status": new_status}
#             yield f"event: status changed\ndata: {json.dumps(res)}\n\n"
#             time.sleep(4)

#     return current_app.response_class(stream_with_context(generate()),mimetype='text/event-stream')
