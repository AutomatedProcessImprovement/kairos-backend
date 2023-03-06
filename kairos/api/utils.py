from dateutil import parser

def expect(input, expectedType, field):
    if isinstance(input, expectedType):
        return input
    raise AssertionError("Invalid input for type", field)

def is_allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['.csv','.xes']

def validate_timestamp(data,columns_definition):
    timeTypes = ['TIMESTAMP','START_TIMESTAMP','END_TIMESTAMP','DATETIME']

    if columns_definition.get(data['column']) in timeTypes:
        data['value'] = parser.parse(data['value']).strftime('%Y-%m-%dT%H:%M:%SZ')

    return data['value']
