from flask import Blueprint, jsonify
import kairos.models.cases_model as cases_db
import kairos.models.event_logs_model as event_logs_db

from flask_cors import CORS

cases_api = Blueprint('cases_api','cases_api',url_prefix='/cases')

CORS(cases_api)

@cases_api.route('')
def get_cases():
    try:
        c = cases_db.get_cases()
        return jsonify(cases = c),200
    except Exception as e:
        return jsonify(error=str(e)),400
    
@cases_api.route('event_logs/<event_log_id>/cases')
def get_cases_by_log(event_log_id):
    try:
        c = cases_db.get_cases_by_log_id(event_log_id)
        return jsonify(cases = c),200
    except Exception as e:
        return jsonify(error=str(e)),400

@cases_api.route('cases/<case_id>')
def get_case(case_id):
    try:
        c = cases_db.get_case(case_id)
        return jsonify(case = c)
    except Exception as e:
        return jsonify(error=str(e)),400
