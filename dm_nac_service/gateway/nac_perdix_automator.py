import os
import shutil

import requests
import json
from fastapi.encoders import jsonable_encoder

from datetime import datetime
from dm_nac_service.resource.log_config import logger
from dm_nac_service.resource.generics import response_to_dict, hanlde_response_body, hanlde_response_status
from fastapi.responses import JSONResponse
from dm_nac_service.data.database import insert_logs, insert_logs_all
# from gateway.lotuspay_source import lotus_pay_post_source5
from dm_nac_service.commons import get_env_or_fail


PERDIX_SERVER = 'perdix-server'


async def perdix_post_login():
    """ Generic Post Method for perdix login """
    try:
        validate_url = get_env_or_fail(PERDIX_SERVER, 'perdix-base-url', PERDIX_SERVER + ' base-url not configured')
        username = get_env_or_fail(PERDIX_SERVER, 'username', PERDIX_SERVER + ' username not configured')
        # username = 'ramesh'
        password = get_env_or_fail(PERDIX_SERVER, 'password', PERDIX_SERVER + ' password not configured')
        url = validate_url + f'/oauth/token?client_id=application&client_secret=mySecretOAuthSecret&grant_type=password&password={password}&scope=read+write&skip_relogin=yes&username={username}'
        str_url = str(url)

        login_context_response = requests.post(url)
        login_context_dict = response_to_dict(login_context_response)

        # Checking for successful login
        if(login_context_response.status_code == 200):
            access_token = login_context_dict.get('access_token')

            log_id = await insert_logs(str_url, 'PERDIX', '', login_context_response.status_code,
                                       login_context_response.content, datetime.now())
            # result = access_token
            result = JSONResponse(status_code=200, content={"access_token": access_token})
            print('*********************************** SUCCESSFULLY LOGGED INTO PERDIX  ***********************************')
        else:
            print(
                '*********************************** FAILURE LOGGED INTO PERDIX  ***********************************')
            log_id = await insert_logs(str_url, 'PERDIX', 'LOGIN', login_context_response.status_code,
                                       login_context_response.content, datetime.now())

            result = JSONResponse(status_code=500, content=login_context_dict)
            print('getting eeror from login ',login_context_dict )


    except Exception as e:
        logger.exception(f"{datetime.now()} - Issue with perdix_post_login function, {e.args[0]}")
        print('*********************************** FAILURE LOGGED INTO PERDIX  ***********************************')
        log_id = await insert_logs(str_url, 'PERDIX', 'LOGIN', e.args[0],
                                   e.args[0], datetime.now())
        result = JSONResponse(status_code=500, content={"message": f"Error Occurred at Perdix Login - {e.args[0]}"})

    return result


async def perdix_fetch_loan(loan_id):
    """ Generic Post Method for perdix fetch customer """
    try:
        validate_url = get_env_or_fail(PERDIX_SERVER, 'perdix-base-url', PERDIX_SERVER + ' base-url not configured')
        url = validate_url + f'/api/individualLoan/{loan_id}'
        str_url = str(url)


        login_token = await perdix_post_login()

        fetch_loan_response_status = hanlde_response_status(login_token)
        fetch_loan_response_body = hanlde_response_body(login_token)

        # If Login is success
        if(fetch_loan_response_status == 200):
            login_token = fetch_loan_response_body.get('access_token')
            headers = {
                "Content-Type": "application/json",
                "Content-Length": "0",
                "User-Agent": 'My User Agent 1.0',
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Authorization": f"bearer {login_token}"
            }

            loan_context_response = requests.get(url, headers=headers)
            # If Loan ID is present
            if(loan_context_response.status_code == 200):
                print('loan_context_response', loan_context_response.content)
                loan_context_response_content = loan_context_response.content
                loan_context_dict = json.loads(loan_context_response_content.decode('utf-8'))
                # loan_context_dict = response_to_dict(loan_context_response)
                log_id = await insert_logs_all(str_url, 'GET', 'NAC', str(loan_id),
                                           loan_context_response.status_code,
                                           str(loan_context_dict), datetime.now())

                print('*********************************** SUCCESSFULLY FETCHED LOAN INFO FROM PERDIX ***********************************', loan_context_dict)
                # result = loan_context_dict
                result = JSONResponse(status_code=200, content=loan_context_dict)
            else:
                response = loan_context_response.content.decode('utf-8')
                log_id = await insert_logs(str_url, 'PERDIX', 'Unable to find loan details', loan_context_response.status_code,
                                           response, datetime.now())
                not_found_response = {"message": "Loan Not found in Perdix"}
                result = JSONResponse(status_code=404, content=not_found_response)
        # If Login is Failure
        else:
            fetch_loan_error = fetch_loan_response_body
            log_id = await insert_logs(str_url, 'PERDIX', 'Unable to find loan details', str(fetch_loan_response_body.get('error')),
                                       str(fetch_loan_response_body.get('error_description')), datetime.now())

            result = JSONResponse(status_code=500, content=fetch_loan_error)

    except Exception as e:
        logger.exception(f"{datetime.now()} - Issue with perdix_fetch_loan function, {e.args[0]}")
        print('*********************************** FAILURE FETCHED LOAN INFO FROM PERDIX ***********************************')
        result = JSONResponse(status_code=500,
                              content={"message": f"Error Occurred at Perdix - Fetch Loan - {e.args[0]}"})
    return result


async def perdix_update_loan(loan_data):
    """ Generic put Method to update perdix customer """
    try:
        print('coming here in perdix_update_loan', loan_data)
        validate_url = get_env_or_fail(PERDIX_SERVER, 'perdix-base-url', PERDIX_SERVER + ' base-url not configured')
        url = validate_url + f'/api/individualLoan'
        str_url = str(url)
        login_token = await perdix_post_login()
        login_token_decode = jsonable_encoder(login_token)
        # loan_id = 872384

        response_body = login_token_decode.get('body')
        response_body_json = json.loads(response_body)

        fetch_loan_response_decode_status = login_token_decode.get('status_code')

        # If login is success
        if (fetch_loan_response_decode_status == 200):
            login_token = response_body_json.get('access_token')
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
            loan_update_response = requests.put(url, json=loan_data, headers=headers)
            loan_update_response_dict = response_to_dict(loan_update_response)
            # If loan update success
            if(loan_update_response.status_code == 200):
                print('***** SUCCESSFULLY UPDATED LOAN INFO TO PERDIX *****')
                log_id = await insert_logs_all(str_url, 'PUT', 'PERDIX', 'perdix_update_loan', str(loan_update_response.status_code),
                                           str(loan_update_response.content), datetime.now())

                result = JSONResponse(status_code=200, content=loan_update_response_dict)
            else:
                logger.error(f"***** UNABLE TO UPDATE LOAN IN PERDIX - {loan_update_response_dict} *****")
                log_id = await insert_logs_all(str_url, 'PUT', 'PERDIX', 'perdix_update_loan',
                                           str(loan_update_response.status_code),
                                           str(loan_update_response.content), datetime.now())
                loan_update_unsuccess = {"error": 'Error from Perdix', "error_description": loan_update_response_dict}
                result = JSONResponse(status_code=500, content=loan_update_unsuccess)
        else:
            response_body = login_token_decode.get('body')
            response_body_json = json.loads(response_body)
            response_body_error = response_body_json.get('error')
            response_body_description = response_body_json.get('error_description')
            log_id = await insert_logs(str_url, 'PERDIX', 'perdix_update_loan', str(response_body_error),
                                       str(response_body_description), datetime.now())
            login_unsuccess = {"error": response_body_error, "error_description": response_body_description}
            result = JSONResponse(status_code=500, content=login_unsuccess)
            print('unsuccess login')

    except Exception as e:
        logger.exception(f"{datetime.now()} - Issue with perdix_update_loan function, {e.args[0]}")
        print(
            '*********************************** FAILED UPDATING LOAN INFO TO PERDIX ***********************************')
        result = JSONResponse(status_code=500, content={"message": f"Error Occurred at Perdix - Update Loan - {e.args[0]}"})
    return result


async def download_file_from_stream(
    doc_id: str
):
    try:
        validate_url = get_env_or_fail(PERDIX_SERVER, 'perdix-base-url',
                                       PERDIX_SERVER + ' perdix-base-url not configured')
        url = validate_url + f'/api/stream/{doc_id}'
        print('url - is ', url)

        download_file_response = requests.get(url)
        print('response  - is ', download_file_response)
        if(download_file_response.status_code == 200):
            download_file_response_headers = download_file_response.headers
            download_file_response_headers_content = download_file_response_headers.get('Content-Disposition')
            find_filename = download_file_response_headers_content.split('filename=', 1)
            found_filename = find_filename[1]
            found_file_ext = found_filename.split('.')
            new_file_name = doc_id + '.' + found_file_ext[1]
            print('FOUND THE FILE', found_filename, found_file_ext, new_file_name)

            file_path = os.path.abspath(('./static/'))

            with open(new_file_name, 'wb') as f:
                f.write(download_file_response.content)
                basename = f.name
                print('-=================', basename)
                move_item = shutil.copy(basename, file_path)
                print("----------------move", move_item)
                if os.path.exists(move_item):
                    remove = os.remove(basename)
                else:
                    print("------file_path------", file_path)
                    print("file is not there")
                    move_item = shutil.move(basename, file_path)
            # download_file_response_headers_json = json.loads(download_file_response_headers)
            result = JSONResponse(status_code=200,content={"filename": new_file_name})
            print('RESPONSE FROM FILE DOWNLOAD ', result)
        else:
            download_file_response_json = json.loads(download_file_response.content.decode('utf-8'))
            app_log_error = {"error": 'NAC', "error_description": download_file_response_json}
            print('NO DOCUMENT FOOUND', download_file_response_json)
            result = JSONResponse(status_code=404, content=app_log_error)
    except Exception as e:
        logger.exception(f"{datetime.now()} - Issue with perdix_update_loan function, {e.args[0]}")
        print('***** FAILED DOWNLOADING FILE FROM PERDIX *****')
        result = JSONResponse(status_code=500,content={"message": f"Error Occurred at Perdix - Update Loan - {e.args[0]}"})
    return result