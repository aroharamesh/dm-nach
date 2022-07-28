import json
from fastapi.encoders import jsonable_encoder

def response_to_dict(response):
    """Converting bytes response to python dictionary"""
    response_content = response.content
    response_decode = response_content.decode("UTF-8")
    json_acceptable_string = response_decode.replace("'", "\"")
    convert_to_json = json.loads(json_acceptable_string)
    response_dict = dict(convert_to_json)
    return response_dict


def tuple_to_dict(tup, di):
    for a, b in tup:
        print('coming inside tuple to dict')
        di.setdefault(a, []).append(b)
    return di


def array_to_dict(lst):
    res_dct = {lst[i]: lst[i + 1] for i in range(0, len(lst), 2)}
    return res_dct


def handle_none(var, val):
    if(var is None):
        result = val
    else:
        result = var
    return result


def hanlde_response_body(body_data):
    body_data_decode = jsonable_encoder(body_data)
    response_body = body_data_decode.get('body')
    if 'error' in response_body:
        response_body_json = json.loads(response_body)
        response_body_error = response_body_json.get('error')
        response_body_description = response_body_json.get('error_description')
        response_to_return = {"error": response_body_error, "error_description": response_body_description}
        print('printing response_body inside generic', response_to_return)
    else:
        response_body_string = response_body
        response_to_return = json.loads(response_body_string)
        print('printing response_body inside generic', response_to_return)
    return response_to_return


def hanlde_response_status(body_data):
    body_data_decode = jsonable_encoder(body_data)
    response_body_status = body_data_decode.get('status_code')
    print('printing response_body inside generic', response_body_status)
    return response_body_status
