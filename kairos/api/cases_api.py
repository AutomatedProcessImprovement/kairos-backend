from flask import Blueprint, jsonify
import kairos.models.cases_model as cases_db

from flask_cors import CORS

cases_api = Blueprint('cases_api','cases_api',url_prefix='/api')

CORS(cases_api)

@cases_api.route('/cases')
def get_cases():
    try:
        c = cases_db.get_cases()
        return jsonify(cases = list(c))
    except Exception as e:
        return jsonify(error=str(e)),400
    
@cases_api.route('event_logs/<file_id>/cases')
def get_cases_by_log(file_id):
    try:
        c = cases_db.get_cases_by_log(file_id)
        return jsonify(cases = list(c)),200
    except Exception as e:
        return jsonify(error=str(e)),400

@cases_api.route('event_logs/<file_id>/cases/<case_id>')
def get_case(file_id,case_id):
    try:
        c = cases_db.get_case_by_log(file_id,case_id)
        return jsonify(case = c)
    except Exception as e:
        return jsonify(error=str(e)),400
