from flask import Blueprint
from flask_cors import CORS

import kairos.services.event_logs_service as event_logs_service

event_logs_api = Blueprint('event_logs_api','event_logs_api',url_prefix='/event_logs')

CORS(event_logs_api)

event_logs_api.route('', methods=['GET'])(event_logs_service.get_logs)
event_logs_api.route('', methods=['POST'])(event_logs_service.save_log)

event_logs_api.route('/<event_log_id>',methods=['GET'])(event_logs_service.get_log)

event_logs_api.route('/<event_log_id>', methods=['DELETE'])(event_logs_service.delete_log)

event_logs_api.route('/<event_log_id>/parameters',methods=['GET'])(event_logs_service.get_log_parameters)
event_logs_api.route('/<event_log_id>/parameters',methods=['POST'])(event_logs_service.define_log_parameters)

event_logs_api.route('/<event_log_id>/column_types', methods=['PUT'])(event_logs_service.define_log_column_types)

# Project

event_logs_api.route('/<event_log_id>/status',methods=['GET'])(event_logs_service.get_project_status)

event_logs_api.route('/<event_log_id>/simulate/start', methods=['PUT'])(event_logs_service.start_simulation)
event_logs_api.route('/<event_log_id>/simulate/stop', methods=['PUT'])(event_logs_service.stop_simulation)

event_logs_api.route('/<event_log_id>/stream/clear', methods=['PUT'])(event_logs_service.clear_stream)