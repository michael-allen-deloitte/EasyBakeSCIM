import base64
import flask

from SCIM import config

headerName = config['Auth']['headerName']
headerValue = config.get('Auth', 'headerValue')

def authenticate(headers, type='Header'):
    if type.lower() == 'header':
        try:
            return headers[headerName] == headerValue
        except:
            return False
    elif type.lower() == "basic":
        unpw = str(base64.b64decode(headers['Authorization'].split(' ')[1]))
        username = unpw.split(':')[0].replace("'", '')[1:]
        password = unpw.split(':')[1].replace("'", '')
        return username == headerName and password == headerValue
    else:
        raise ValueError("The authentication type: %s is not recognized" % type)


def scim_error(message, status_code=500, stack_trace:str = None):
    rv = {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
        "detail": message,
        "status": status_code
    }
    if stack_trace is not None:
        rv['stack_trace'] = stack_trace
    return flask.make_response(rv, status_code)