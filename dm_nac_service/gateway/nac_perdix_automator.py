import requests
import json
from datetime import datetime

from dm_nac_service.resource.generics import response_to_dict
from fastapi.responses import JSONResponse
from dm_nac_service.data.database import insert_logs
# from gateway.lotuspay_source import lotus_pay_post_source5
from dm_nac_service.commons import get_env_or_fail


PERDIX_SERVER = 'perdix-server'


async def perdix_post_login():
    """ Generic Post Method for perdix login """
    try:
        validate_url = get_env_or_fail(PERDIX_SERVER, 'perdix-base-url', PERDIX_SERVER + ' base-url not configured')
        username = get_env_or_fail(PERDIX_SERVER, 'username', PERDIX_SERVER + ' username not configured')
        password = get_env_or_fail(PERDIX_SERVER, 'password', PERDIX_SERVER + ' password not configured')
        # url = validate_url + f'/{context}/'
        url = validate_url + f'/oauth/token?client_id=application&client_secret=mySecretOAuthSecret&grant_type=password&password={password}&scope=read+write&skip_relogin=yes&username={username}'
        # print(url)
        str_url = str(url)
        login_context_response = requests.post(url)
        # print(login_context_response)
        login_context_dict = response_to_dict(login_context_response)
        access_token = login_context_dict.get('access_token')
        log_id = await insert_logs(str_url, 'PERDIX', 'LOGIN', login_context_response.status_code,
                                   login_context_response.content, datetime.now())
        print('*********************************** SUCCESSFULLY LOGGED INTO PERDIX  ***********************************')
        result = access_token

    except Exception as e:
        print('*********************************** FAILURE LOGGED INTO PERDIX  ***********************************')
        log_id = await insert_logs(str_url, 'PERDIX', 'LOGIN', login_context_response.status_code,
                                   login_context_response.content, datetime.now())
        result = JSONResponse(status_code=500, content={"message": f"Error Occurred at Perdix Login - {e.args[0]}"})

    return result


async def perdix_fetch_loan(loan_id):
    """ Generic Post Method for perdix fetch customer """
    try:
        validate_url = get_env_or_fail(PERDIX_SERVER, 'perdix-base-url', PERDIX_SERVER + ' base-url not configured')

        username = get_env_or_fail(PERDIX_SERVER, 'username', PERDIX_SERVER + ' username not configured')
        password = get_env_or_fail(PERDIX_SERVER, 'password', PERDIX_SERVER + ' password not configured')


        login_token = await perdix_post_login()
        url = validate_url + f'/api/individualLoan/{loan_id}'

        headers = {
            "Content-Type": "application/json",
            "Content-Length": "0",
            "User-Agent": 'My User Agent 1.0',
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Authorization": f"bearer {login_token}"
        }
        str_url = str(url)
        loan_context_response = requests.get(url, headers=headers)
        print('FETCH LOAN FROM PERDIX ', loan_context_response)
        if(loan_context_response.status_code == 200):

            loan_context_dict = response_to_dict(loan_context_response)
            # log_id = await insert_logs(str_url, 'PERDIX', 'FETCH-CUSTOMER', customer_context_response.status_code,
            #                            customer_context_response.content, datetime.now())
            print('*********************************** SUCCESSFULLY FETCHED LOAN INFO FROM PERDIX ***********************************')
            result = loan_context_dict
        else:
            loan_context_dict = response_to_dict(loan_context_response)
            print('6 - Error in creating dedupe from NAC endpoint', loan_context_dict)
            log_id = await insert_logs(str_url, 'PERDIX', 'Unable to find loan details', loan_context_dict.status_code,
                                       loan_context_dict.content, datetime.now())

            result = JSONResponse(status_code=500, content=loan_context_dict)
    except Exception as e:
        print('*********************************** FAILURE FETCHED LOAN INFO FROM PERDIX ***********************************')
        log_id = await insert_logs(str_url, 'PERDIX', 'FETCH-LOAN', loan_context_response.status_code,
                                   loan_context_response.content, datetime.now())
        result = JSONResponse(status_code=500,
                              content={"message": f"Error Occurred at Perdix - Fetch Loan - {e.args[0]}"})
    return result


async def perdix_update_loan(loan_data):
    """ Generic put Method to update perdix customer """
    try:
        validate_url = get_env_or_fail(PERDIX_SERVER, 'perdix-base-url', PERDIX_SERVER + ' base-url not configured')
        # print('coming after validate url')
        username = get_env_or_fail(PERDIX_SERVER, 'username', PERDIX_SERVER + ' username not configured')
        password = get_env_or_fail(PERDIX_SERVER, 'password', PERDIX_SERVER + ' password not configured')

        login_token = await perdix_post_login()

        # Fetch the loan
        # get_loan_info = perdix_fetch_loan(loan_id)

        url = validate_url + f'/api/individualLoan'

        headers = {
            "Content-Type": "application/json",
            "Content-Length": "0",
            "User-Agent": 'My User Agent 1.0',
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Authorization": f"bearer {login_token}"
        }
        str_url = str(url)
        # print('printing endpoint url ', url)
        # print('printing endpoint url ', loan_data)
        loan_update_response = requests.put(url, json=loan_data, headers=headers)
        # print('printing the loan update response from perdix', loan_update_response.status_code, loan_update_response.content)
        loan_update_response_dict = response_to_dict(loan_update_response)
        print('*********************************** SUCCESSFULLY UPDATED LOAN INFO TO PERDIX ***********************************')
        result = loan_update_response_dict
        # if(loan_update_response.status_code == 400):
        #     response_content = loan_update_response.content
        #     result = json.loads(response_content.decode('utf-8'))
        #     print('200 OK result - ', result)
        # else:
        #     loan_context_dict = response_to_dict(loan_update_response)
        #     result = loan_context_dict
        #     print('NOT 200 OK result - ', result)

    except Exception as e:
        # print(e.args[0])
        print(
            '*********************************** FAILED UPDATING LOAN INFO TO PERDIX ***********************************')
        log_id = await insert_logs(url, 'PERDIX', 'UPDATE-LOAN', loan_update_response.status_code,
                                   loan_update_response.content, datetime.now())
        result = JSONResponse(status_code=500,
                              content={"message": f"Error Occurred at Perdix - Update Loan - {e.args[0]}"})
    return result

