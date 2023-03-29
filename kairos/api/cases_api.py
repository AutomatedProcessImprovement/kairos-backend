from flask import Blueprint
from kairos.services import cases_service

from flask_cors import CORS

cases_api = Blueprint('cases_api','cases_api',url_prefix='/cases')

CORS(cases_api)

cases_api.route('',methods=['GET'])(cases_service.get_cases)

cases_api.route('/<case_id>',methods=['GET'])(cases_service.get_case)