import kairos.models.cases_model as cases_db
from flask import jsonify


def get_cases():
    try:
        c = cases_db.get_cases()
        return jsonify(cases = c),200
    except Exception as e:
        return jsonify(error=str(e)),400
    
def get_cases_by_log(event_log_id):
    try:
        c = cases_db.get_cases_by_log_id(event_log_id)
        return jsonify(cases = c),200
    except Exception as e:
        return jsonify(error=str(e)),400

def get_case(case_id):
    try:
        c = cases_db.get_case(case_id)
        return jsonify(case = c)
    except Exception as e:
        return jsonify(error=str(e)),400