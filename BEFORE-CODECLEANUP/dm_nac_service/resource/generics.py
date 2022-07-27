import json


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