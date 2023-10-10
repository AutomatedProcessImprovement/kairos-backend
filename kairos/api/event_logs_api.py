from flask import Blueprint
from flask_cors import CORS

from kairos.services import event_logs_service, cases_service,openai_service

event_logs_api = Blueprint('event_logs_api','event_logs_api',url_prefix='/event_logs')

CORS(event_logs_api)

event_logs_api.route('/<event_log_id>/cases',methods=['GET'])(cases_service.get_cases_by_log)

event_logs_api.route('/<event_log_id>/cases/<case_completion>',methods=['GET'])(cases_service.get_cases_by_log_and_completion)

event_logs_api.route('', methods=['GET'])(event_logs_service.get_logs)

event_logs_api.route('', methods=['POST'])(event_logs_service.save_log)

event_logs_api.route('/<event_log_id>',methods=['GET'])(event_logs_service.get_log)

event_logs_api.route('/<event_log_id>', methods=['DELETE'])(event_logs_service.delete_log)

event_logs_api.route('/<event_log_id>/column_types', methods=['PUT'])(event_logs_service.define_log_column_types)

event_logs_api.route('/<event_log_id>/parameters',methods=['GET'])(event_logs_service.get_log_parameters)

event_logs_api.route('/<event_log_id>/parameters',methods=['POST'])(event_logs_service.define_log_parameters)

event_logs_api.route('/<event_log_id>/prescriptions',methods=['GET'])(event_logs_service.get_log_prescriptions)

# Project

event_logs_api.route('/<event_log_id>/status',methods=['GET'])(event_logs_service.get_project_status)

event_logs_api.route('/<event_log_id>/simulate/start', methods=['PUT'])(event_logs_service.start_simulation)

event_logs_api.route('/<event_log_id>/simulate/stop', methods=['PUT'])(event_logs_service.stop_simulation)

event_logs_api.route('/<event_log_id>/simulate/clear', methods=['PUT'])(event_logs_service.clear_stream)

event_logs_api.route('/<event_log_id>/results', methods=['GET'])(event_logs_service.get_static_results)

# Openai

event_logs_api.route('/<event_log_id>/openai/history', methods=['GET'])(openai_service.get_log_openai_history)

event_logs_api.route('/<event_log_id>/openai', methods=['POST'])(openai_service.ask_openai_question)