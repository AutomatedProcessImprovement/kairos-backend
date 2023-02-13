import json
import numpy as np

def expect(input, expectedType, field):
    if isinstance(input, expectedType):
        return input
    raise AssertionError("Invalid input for type", field)

def is_allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['.csv','.xes']

def initial():
    with open('data.json') as f:
        data = json.load(f)
        kpi = data.get('kpi')
        for case in data['cases']:
            case["status"] = "Completed" if [obj for obj in case["activities"] if obj["name"] == "End Event"] else "Open"
        return data, kpi

def get_case_attributes(file,case_attributes):
    dic = {}
    for attr in case_attributes:
        ind = file.get('columns_header').index(attr)
        df = np.array(file.get('columns_data'))
        df = df.transpose()
        col = list(df[ind])
        val = max(set(col), key = col.count)
        dic[attr] = val
    return dic