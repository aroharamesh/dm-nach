from datetime import datetime
import requests
import time
from dm_nac_service.resource.generics import response_to_dict
from fastapi.responses import JSONResponse
from dm_nac_service.data.database import insert_logs
from dm_nac_service.commons import get_env_or_fail
from dm_nac_service.resource.generics import response_to_dict
from dm_nac_service.resource.log_config import logger
import json

NAC_SERVER = 'northernarc-server'


async def nac_sanction(context, data):
    """ Generic Post Method for dedupe """
    try:
        validate_url = get_env_or_fail(NAC_SERVER, 'base-url', NAC_SERVER + ' base-url not configured')
        api_key = get_env_or_fail(NAC_SERVER, 'api-key', NAC_SERVER + ' api-key not configured')
        group_key = get_env_or_fail(NAC_SERVER, 'group-key', NAC_SERVER + ' group-key not configured')
        originator_id = get_env_or_fail(NAC_SERVER, 'originator-id', NAC_SERVER + 'originator ID not configured')
        sector_id = get_env_or_fail(NAC_SERVER, 'sector-id', NAC_SERVER + 'Sector ID not configured')
        url = validate_url + f'/po/{context}?originatorId={originator_id}&sectorId={sector_id}'
        print('4 - Received data from sanction - ', data)
        # print('nac sanction url', url)
        str_url = str(url)
        # str_data = data.dict()
        headers = {
            "API-KEY": api_key,
            "GROUP-KEY": group_key,
            "Content-Type": "application/json",
            "Content-Length": "0",
            "User-Agent": 'My User Agent 1.0',
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
        print('*********** printin sanction data to be posted', data)
        sanction_context_response = requests.post(url, json=data, headers=headers)
        if (sanction_context_response.status_code == 200):
            log_id = await insert_logs(str_url, 'NAC', str(data), sanction_context_response.status_code,
                                       sanction_context_response.content, datetime.now())
            response_content = sanction_context_response.content
            sanction_context_response_dict = response_to_dict(sanction_context_response)
            res = json.loads(response_content.decode('utf-8'))
            log_id = await insert_logs(str_url, 'NAC', str(data), sanction_context_response.status_code,
                                       sanction_context_response.content, datetime.now())
            result = JSONResponse(status_code=200, content=sanction_context_response_dict)
        else:
            sanction_context_response_dict = response_to_dict(sanction_context_response)
            print('6 - Error in creating dedupe from NAC endpoint', sanction_context_response_dict)
            log_id = await insert_logs(str_url, 'NAC', str(data), sanction_context_response.status_code,
                                       sanction_context_response.content, datetime.now())

            result = JSONResponse(status_code=500, content=sanction_context_response_dict)
        # result = sanction_context_response_dict
        print(
            '*********************************** SUCCESSFULLY POSTED SANCTION DATA TO NAC ENDPOINT  ***********************************')
    except Exception as e:
        logger.exception(f"{datetime.now()} - Issue with nac_sanction function, {e.args[0]}")
        result = JSONResponse(status_code=500,content={"message": f"Error Occurred at Northern Arc Post Method - {e.args[0]}"})

    return result


async def nac_sanction_fileupload(context, data):
    try:
        validate_url = get_env_or_fail(NAC_SERVER, 'base-url', NAC_SERVER + ' base-url not configured')
        api_key = get_env_or_fail(NAC_SERVER, 'api-key', NAC_SERVER + ' api-key not configured')
        group_key = get_env_or_fail(NAC_SERVER, 'group-key', NAC_SERVER + ' group-key not configured')
        originator_id = get_env_or_fail(NAC_SERVER, 'originator-id', NAC_SERVER + 'originator ID not configured')
        sector_id = get_env_or_fail(NAC_SERVER, 'sector-id', NAC_SERVER + 'Sector ID not configured')
        url = validate_url + f'/po/{context}?originatorId={originator_id}&sectorId={sector_id}'
        # print('nac sanction url', url)
        str_url = str(url)
        # str_data = data.dict()
    except Exception as e:
        log_id = await insert_logs('GATEWAY', 'NAC', 'nac_sanction_fileupload', {e.args[0]},
                                   '', datetime.now())
        result = JSONResponse(status_code=500,
                              content={"message": f"Error Occurred at Northern Arc Post Method - {e.args[0]}"})


async def nac_get_sanction(context, customer_id):
    try:

        validate_url = get_env_or_fail(NAC_SERVER, 'base-url', NAC_SERVER + ' base-url not configured')
        api_key = get_env_or_fail(NAC_SERVER, 'api-key', NAC_SERVER + ' api-key not configured')
        group_key = get_env_or_fail(NAC_SERVER, 'group-key', NAC_SERVER + ' group-key not configured')
        originator_id = get_env_or_fail(NAC_SERVER, 'originator-id', NAC_SERVER + 'originator ID not configured')
        sector_id = get_env_or_fail(NAC_SERVER, 'sector-id', NAC_SERVER + 'Sector ID not configured')
        url = validate_url + f'/po/{context}?originatorId={originator_id}&customerId={customer_id}'
        headers = {
            "API-KEY": api_key,
            "GROUP-KEY": group_key,
            "Content-Type": "application/json",
            "Content-Length": "0",
            "User-Agent": 'My User Agent 1.0',
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "accept": "*/*"
        }
        # print('nac sanction url', url)
        sanction_get_response = requests.get(url, headers=headers)
        # time.sleep(5)
        # print('response from get sanction gateway ', sanction_get_response.content)
        sanction_get_response_dict = response_to_dict(sanction_get_response)
        print('response from get sanction gateway ', sanction_get_response_dict)
        str_url = str(url)
        # str_data = data.dict()
        result = sanction_get_response_dict

    except Exception as e:

        result = JSONResponse(status_code=500,
                              content={"message": f"Error Occurred at Northern Arc Post Method - {e.args[0]}"})

    return result