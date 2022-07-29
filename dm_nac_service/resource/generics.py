import json
from datetime import datetime
from fastapi.encoders import jsonable_encoder
from dm_nac_service.data.database import get_database
from dm_nac_service.resource.log_config import logger

def response_to_dict(response):
    try:
        """Converting bytes response to python dictionary"""
        response_content = response.content
        response_decode = response_content.decode("UTF-8")
        json_acceptable_string = response_decode.replace("'", "\"")
        convert_to_json = json.loads(json_acceptable_string)
        response_dict = dict(convert_to_json)
        return response_dict
    except Exception as e:
        logger.exception(f"{datetime.now()} - Exception inside response_to_dict from generics {e.args[0]}")


def tuple_to_dict(tup, di):
    try:
        for a, b in tup:
            print('coming inside tuple to dict')
            di.setdefault(a, []).append(b)
        return di
    except Exception as e:
        logger.exception(f"{datetime.now()} - Exception inside tuple_to_dict from generics {e.args[0]}")


def array_to_dict(lst):
    try:
        res_dct = {lst[i]: lst[i + 1] for i in range(0, len(lst), 2)}
        return res_dct
    except Exception as e:
        logger.exception(f"{datetime.now()} - Exception inside array_to_dict from generics {e.args[0]}")


def handle_none(var, val):
    if(var is None):
        result = val
    else:
        result = var
    return result


def hanlde_response_body(body_data):
    try:
        body_data_decode = jsonable_encoder(body_data)
        response_body = body_data_decode.get('body')
        if 'error' in response_body:
            response_body_json = json.loads(response_body)
            response_body_error = response_body_json.get('error')
            response_body_description = response_body_json.get('error_description')
            response_to_return = {"error": response_body_error, "error_description": response_body_description}
        else:
            response_body_string = response_body
            response_to_return = json.loads(response_body_string)
        return response_to_return
    except Exception as e:
        logger.exception(f"{datetime.now()} - Exception inside hanlde_response_body from generics {e.args[0]}")


def hanlde_response_status(body_data):
    try:
        body_data_decode = jsonable_encoder(body_data)
        response_body_status = body_data_decode.get('status_code')
        return response_body_status
    except Exception as e:
        logger.exception(f"{datetime.now()} - Exception inside hanlde_response_status from generics {e.args[0]}")


async def fetch_data_from_db(table):
    try:
        database = get_database()
        query = table.select()
        record_array = await database.fetch_all(query)
        return record_array
    except Exception as e:
        logger.exception(f"{datetime.now()} - Exception inside fetch_data_from_db from generics {e.args[0]}")
