import kairos.models.cases_model as cases_db

from flask import jsonify, current_app, request

def get_cases():
    try:
        c = cases_db.get_cases()
        current_app.logger.info(f'{request.method} {request.path} 200')
        return jsonify(cases = c),200
    except Exception as e:
        current_app.logger.error(f'{request.method} {request.path} 400 - {e}')
        return jsonify(error=str(e)),400

def get_cases_by_log(event_log_id):
    try:
        c = cases_db.get_cases_by_log_id(event_log_id)
        current_app.logger.info(f'{request.method} {request.path} 200')
        return jsonify(cases = c),200
    except Exception as e:
        current_app.logger.error(f'{request.method} {request.path} 400 - {e}')
        return jsonify(error=str(e)),400

def get_case(case_id):
    try:
        c = cases_db.get_case(case_id)
        current_app.logger.info(f'{request.method} {request.path} 200')
        return jsonify(case = c)
    except Exception as e:
        current_app.logger.error(f'{request.method} {request.path} 400 - {e}')
        return jsonify(error=str(e)),400
    