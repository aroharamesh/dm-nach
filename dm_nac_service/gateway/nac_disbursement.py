import json
import requests

from datetime import datetime
from dm_nac_service.resource.generics import response_to_dict
from fastapi.responses import JSONResponse
from dm_nac_service.data.database import insert_logs
from dm_nac_service.commons import get_env_or_fail
from dm_nac_service.resource.generics import response_to_dict
from dm_nac_service.app_responses.disbursement import disbursement_request_success_response, disbursement_request_error_response1, disbursement_request_error_response2, disbursement_request_error_response3, disbursement_status_success_response1, disbursement_status_success_response2, disbursement_status_error_response1, disbursement_status_error_response2, disbursement_status_error_response3
from dm_nac_service.resource.log_config import logger

NAC_SERVER = 'northernarc-server'


async def nac_disbursement(context, data):
    """ Generic Post Method for Disbursement """
    try:
        validate_url = get_env_or_fail(NAC_SERVER, 'base-url', NAC_SERVER + ' base-url not configured')
        api_key = get_env_or_fail(NAC_SERVER, 'api-key', NAC_SERVER + ' api-key not configured')
        group_key = get_env_or_fail(NAC_SERVER, 'group-key', NAC_SERVER + ' group-key not configured')
        url = validate_url + f'/po/{context}/request'
        str_url = str(url)
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
        # Real Endpoint Test
        disbursement_context_response = requests.post(url, json=data, headers=headers)
        disbursement_context_response_dict = response_to_dict(disbursement_context_response)

        # Fake Success Response to test with disbursement reference id
        disbursement_context_response_dict = disbursement_request_success_response

        # Fake Error Response1 to test
        # disbursement_context_response_dict = disbursement_request_error_response1

        # Fake Error Response2 to test
        # disbursement_context_response_dict = disbursement_request_error_response2

        # Fake Error Response3 to test
        # disbursement_context_response_dict = disbursement_request_error_response3

        if(disbursement_context_response.status_code == 200):

            if(disbursement_context_response_dict['content']['status'] == 'SUCCESS'):
                logger.info(f"***** SUCCESSFULLY POSTED DISBURSEMENT DATA TO NAC ENDPOINT ***** {disbursement_context_response_dict}")
                log_id = await insert_logs(str_url, 'NAC', str(data), disbursement_context_response.status_code,
                                           disbursement_context_response.content, datetime.now())
                result = JSONResponse(status_code=200, content=disbursement_context_response_dict)
            else:
                logger.info(f"***** FAILED RESPONSE FROM DISBURSEMENT DATA TO NAC ENDPOINT ***** {disbursement_context_response_dict}")
                log_id = await insert_logs(str_url, 'NAC', str(data), disbursement_context_response.status_code,
                                           disbursement_context_response.content, datetime.now())
                result = JSONResponse(status_code=200, content=disbursement_context_response_dict)
        else:
            log_id = await insert_logs(str_url, 'NAC', str(data), disbursement_context_response.status_code,
                                       disbursement_context_response.content, datetime.now())
            logger.info(f"***** FAILED RESPONSE FROM DISBURSEMENT DATA TO NAC ENDPOINT ***** {disbursement_context_response_dict}")
            result = JSONResponse(status_code=500, content=disbursement_context_response_dict)
    except Exception as e:
        logger.info('***** FAILED POSTING DISBURSEMENT DATA TO NAC ENDPOINT *****')
        logger.exception(f"{datetime.now()} - Issue with nac_disbursement function, {e.args[0]}")
        result = JSONResponse(status_code=500, content={"message": f"Error Occurred at Northern Arc Post Method - {e.args[0]}"})
    return result


async def disbursement_get_status(context, disbursement_reference_id):
    """ Generic GET Method for Disbursement """
    try:
        # print('coming inside of nac_disbursement_get_status', disbursement_reference_id)
        validate_url = get_env_or_fail(NAC_SERVER, 'base-url', NAC_SERVER + ' base-url not configured')
        api_key = get_env_or_fail(NAC_SERVER, 'api-key', NAC_SERVER + ' api-key not configured')
        group_key = get_env_or_fail(NAC_SERVER, 'group-key', NAC_SERVER + ' group-key not configured')
        originator_id = get_env_or_fail(NAC_SERVER, 'originator-id', NAC_SERVER + 'originator ID not configured')
        url = validate_url + f'/po/{context}/status/originatorId={originator_id}&disbursementReferenceId={disbursement_reference_id}'
        # print('printng the url', url)
        str_url = str(url)
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
        disbursement_status_response = requests.get(url, headers=headers, )
        disbursement_status_response_dict = response_to_dict(disbursement_status_response)
        # print('disbursement_status_response_dict', disbursement_status_response_dict)

        # Fake Success Response1 to test
        # disbursement_status_response_dict = disbursement_request_success_response


        # Fake Success Response1 to test PENNY_DROP AND IN_PROGRESS
        # disbursement_status_response_dict = disbursement_status_success_response1

        # Fake Success Response2 to test with UTR
        disbursement_status_response_dict = disbursement_status_success_response2

        # Fake Error Response1 to test INVALID DISBURSEMENT ID status and message
        # disbursement_status_response_dict = disbursement_status_error_response1

        # Fake Error Response2 to test PENNY_DROP AND FAILED
        # disbursement_status_response_dict = disbursement_status_error_response2

        # Fake Error Response3 to test AMOUNT_DISBURSEMENT AND FAILED
        # disbursement_status_response_dict = disbursement_status_error_response3


        # print('nac_disbursement_get_status', disbursement_context_response_dict)

        result = disbursement_status_response_dict
    except Exception as e:
        log_id = await insert_logs('GATEWAY', 'NAC', 'nac_disbursement', disbursement_status_response_dict.status_code,
                                   disbursement_status_response_dict.content, datetime.now())
        result = JSONResponse(status_code=500,
                              content={"message": f"Error Occurred at Northern Arc Post Method - {e.args[0]}"})
    return result
