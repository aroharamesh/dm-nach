import random
import re
import shutil
import json
import requests
import os
import urllib.request

from fastapi import APIRouter, Depends, status, File, UploadFile, Form, Query
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from datetime import datetime
from databases import Database
from fastapi.exceptions import HTTPException

from dm_nac_service.commons import get_env_or_fail
from dm_nac_service.data.database import get_database, sqlalchemy_engine, insert_logs
from dm_nac_service.gateway.nac_sanction import nac_sanction, nac_sanction_fileupload, nac_get_sanction, upload_file_to_nac
from dm_nac_service.gateway.nac_perdix_automator import download_file_from_stream
from dm_nac_service.routes.dedupe import create_dedupe, find_dedupe
from dm_nac_service.resource.log_config import logger
from dm_nac_service.app_responses.sanction import sanction_request_data, sanction_response_success_data, sanction_response_error_data, sanction_file_upload_response1, sanction_file_upload_response2
from dm_nac_service.data.dedupe_model import (
    dedupe
)
from dm_nac_service.resource.generics import response_to_dict, hanlde_response_body, hanlde_response_status, handle_none
from dm_nac_service.data.sanction_model import (
    SanctionDB,
    SanctionBase,
    CreateSanction,
    sanction,
    FileChoices,
    sanction_fileupload
)

NAC_SERVER = 'northernarc-server'
PERDIX_SERVER = 'perdix-server'

FILE_CHOICES = ['SELFIE', 'AADHAR_XML', 'MITC', 'VOTER_CARD', 'DRIVING_LICENSE', 'SANCTION_LETTER', 'PAN', 'PASSPORT', 'AADHAR_DOC', 'LOAN_APPLICATION', 'LOAN_AGREEMENT']

router = APIRouter()


@router.post("/find-sanction", tags=["Sanction"])
async def find_sanction(
        loan_id
):
    try:
        database = get_database()
        select_query = sanction.select().where(sanction.c.loan_id == loan_id).order_by(sanction.c.id.desc())
        raw_sanction = await database.fetch_one(select_query)
        sanction_dict = {
            "customerId": raw_sanction[1],
            "dedupeRefId": raw_sanction[57]
        }

        print( '*********************************** SUCCESSFULLY FETCHED SANCTION REFERENCE ID FROM DB  ***********************************', sanction_dict)
        result = JSONResponse(status_code=200, content=sanction_dict)
    except Exception as e:
        logger.exception(f"{datetime.now()} - Issue with find_dedupe function, {e.args[0]}")
        print(
            '*********************************** FAILURE FETCHING SANCTION REFERENCE ID FROM DB  ***********************************')
        db_log_error = {"error": 'DB', "error_description": 'Customer ID not found in DB'}
        result = JSONResponse(status_code=500, content=db_log_error)
    return result


@router.post("/sanction", tags=["Sanction"])
async def create_sanction(
    # sanction_data: CreateSanction,
    sanction_data,
    # database: Database = Depends(get_database)
):
    try:
        database = get_database()

        sanction_data['emiWeek'] = 1
        # sanction_data['lastName'] = "Dummy"
        sanction_data['companyName'] = "Dvara"
        # we have occupation which is not matching with NAC default values
        sanction_data['occupation'] = "SELF_EMPLOYED"
        # sanction_data['repaymentFrequency'] = "WEEKLY"
        sanction_data['incomeValidationStatus'] = "SUCCESS"

        # Below is for fake data
        # sanction_dict = sanction_data.dict()

        sm_loan_id = sanction_data['loanId']
        fetch_dedupe_info = await find_dedupe(sm_loan_id)
        fetch_dedupe_info_decode = jsonable_encoder(fetch_dedupe_info)
        fetch_dedupe_info_decode_status = fetch_dedupe_info_decode.get('status_code')
        if(fetch_dedupe_info_decode_status == 200):
            print('FOUND DEDUPE REFERENCE ID', fetch_dedupe_info_decode)
            response_body = fetch_dedupe_info_decode.get('body')
            response_body_json = json.loads(response_body)
            dedupe_reference_id = response_body_json.get('dedupeRefId')
            print('2 - extracted dedupe reference id from DB', fetch_dedupe_info)
            sanction_data['dedupeReferenceId'] = int(dedupe_reference_id)

            sanction_dict = sanction_data

            print('3 - Posting data to NAC create sanction endpoint', sanction_dict)

            # Real API response from NAC
            sanction_response = await nac_sanction('uploadSanctionJSON', sanction_dict)
            print('7 - Getting the dedupe reference from nac_dedupe function - ', sanction_response)
            sanction_response_decode = jsonable_encoder(sanction_response)
            sanction_response_decode_status = sanction_response_decode.get('status_code')
            if(sanction_response_decode_status == 200):

                response_body = sanction_response_decode.get('body')
                response_body_json = json.loads(response_body)

                response_body_json_status = response_body_json.get('content').get('status')
                print('CUSTOMER CREATED SUCCFULLY', response_body_json_status)
                response_body_json__error = response_body_json.get('error')
                if (response_body_json_status == 'SUCCESS'):
                    # customer_id = sanction_response['content']['value']['customerId']
                    customer_id = response_body_json.get('content').get('value').get('customerId')
                    store_record_time = datetime.now()
                    sanction_info = {
                        'customer_id': str(customer_id),
                        'created_date': store_record_time,
                        'mobile': sanction_dict['mobile'],
                        'first_name': sanction_dict['firstName'],
                        'last_name': sanction_dict['lastName'],
                        'father_name': sanction_dict['fatherName'],
                        'gender': sanction_dict['gender'],
                        'id_proof_type_from_partner': sanction_dict['idProofTypeFromPartner'],
                        'id_proof_number_from_partner': sanction_dict['idProofNumberFromPartner'],
                        'address_proof_type_from_partner': sanction_dict['addressProofTypeFromPartner'],
                        'address_proof_number_from_partner': sanction_dict['addressProofNumberFromPartner'],
                        'dob': sanction_dict['dob'],
                        'owned_vehicle': sanction_dict['ownedVehicle'],
                        'curr_door_and_building': sanction_dict['currDoorAndBuilding'],
                        'curr_street_and_locality': sanction_dict['currStreetAndLocality'],
                        'curr_landmark': sanction_dict['currLandmark'],
                        'curr_city': sanction_dict['currCity'],
                        'curr_district': sanction_dict['currDistrict'],
                        'curr_state': sanction_dict['currState'],
                        'curr_pincode': sanction_dict['currPincode'],
                        'perm_door_and_building': sanction_dict['permDoorAndBuilding'],
                        'perm_city': sanction_dict['permCity'],
                        'perm_district': sanction_dict['permDistrict'],
                        'perm_state': sanction_dict['permState'],
                        'perm_pincode': sanction_dict['permPincode'],
                        'occupation': sanction_dict['occupation'],
                        'company_name': sanction_dict['companyName'],
                        'gross_monthly_income': sanction_dict['grossMonthlyIncome'],
                        'net_monthly_income': sanction_dict['netMonthlyIncome'],
                        'income_validation_status': sanction_dict['incomeValidationStatus'],
                        'pan': sanction_dict['pan'],
                        'purpose_of_loan': sanction_dict['purposeOfLoan'],
                        'loan_amount': sanction_dict['loanAmount'],
                        'interest_rate': sanction_dict['interestRate'],
                        'schedule_start_date': sanction_dict['scheduleStartDate'],
                        'first_installment_date': sanction_dict['firstInstallmentDate'],
                        'total_processing_fees': sanction_dict['totalProcessingFees'],
                        'gst': sanction_dict['gst'],
                        'pre_emi_amount': sanction_dict['preEmiAmount'],
                        'emi': sanction_dict['emi'],
                        'emi_date': sanction_dict['emiDate'],
                        'emi_week': sanction_dict['emiWeek'],
                        'repayment_frequency': sanction_dict['repaymentFrequency'],
                        'repayment_mode': sanction_dict['repaymentMode'],
                        'tenure_value': sanction_dict['tenureValue'],
                        'tenure_units': sanction_dict['tenureUnits'],
                        'product_name': sanction_dict['productName'],
                        'primary_bank_account': sanction_dict['primaryBankAccount'],
                        'bank_name': sanction_dict['bankName'],
                        'mode_of_salary': sanction_dict['modeOfSalary'],
                        'client_id': sanction_dict['clientId'],
                        'dedupe_reference_id': sanction_dict['dedupeReferenceId'],
                        'email': sanction_dict['email'],
                        'middle_name': sanction_dict['middleName'],
                        'marital_status': sanction_dict['maritalStatus'],
                        'loan_id': sanction_dict['loanId'],
                    }
                    print('4 - Storing customer Id from NAC Sanction Endpoint to DB', sanction_info)
                    insert_query = sanction.insert().values(sanction_info)
                    print('query', insert_query)
                    sanction_id = await database.execute(insert_query)
                    print('5 - Saved Sanction information to DB', sanction_info)
                    result = JSONResponse(status_code=200, content={"customerid": customer_id})
                    print('6 - Update customer id to udf42 in Perdix', sanction_info)

                    return result
                else:
                    log_id = await insert_logs('DB', 'NAC', 'DEDUPE', sanction_response.status_code,
                                               sanction_response.content, datetime.now())
                    result = JSONResponse(status_code=500, content={"message": f"Issue with Northern Arc API"})
            else:
                print('CUSTOMER NOT CREATED SUCCFULLY', sanction_response_decode)
                result = JSONResponse(status_code=500, content=sanction_response_decode)
            print('5 - Response from NAC Sanction Endpoint', sanction_response)

        else:
            response_body = fetch_dedupe_info_decode.get('body')
            response_body_json = json.loads(response_body)
            response_body_error = response_body_json.get('error')
            response_body_error_description = response_body_json.get('error_description')
            app_log_error = {"error": response_body_error, "error_description": response_body_error_description}
            logger.error(f"{datetime.now()} - create_sanction - 190 - {app_log_error}")
            result = fetch_dedupe_info_decode

    except Exception as e:
        logger.exception(f"{datetime.now()} - Issue with create_sanction function, {e.args[0]}")
        result = JSONResponse(status_code=500, content={"message": f"Issue with Northern Arc API, {e.args[0]}"})
    return result


@router.post("/fileupload", tags=["Sanction"])
async def fileupload_sanction(
        customer_id: str, file: UploadFile, file_type: str = Query("File Types", enum=FILE_CHOICES),  database: Database = Depends(get_database)
):
    try:
        validate_url = get_env_or_fail(NAC_SERVER, 'base-url', NAC_SERVER + ' base-url not configured')
        api_key = get_env_or_fail(NAC_SERVER, 'api-key', NAC_SERVER + ' api-key not configured')
        group_key = get_env_or_fail(NAC_SERVER, 'group-key', NAC_SERVER + ' group-key not configured')
        originator_id = get_env_or_fail(NAC_SERVER, 'originator-id', NAC_SERVER + 'originator ID not configured')
        sector_id = get_env_or_fail(NAC_SERVER, 'sector-id', NAC_SERVER + 'Sector ID not configured')
        file_stream_url = get_env_or_fail(PERDIX_SERVER, 'perdix-stream-url', PERDIX_SERVER + 'Stream URL is not configured')
        url = validate_url + f'/po/uploadFile?originatorId={originator_id}&fileType={file_type}&customerId={customer_id}'
        image_id = '94d150e4-6232-4f5e-a341-494d76c5c4bf'
        file_url = file_stream_url + image_id
        tmp_file = "./static/" + image_id
        print('priting temporary file', tmp_file)
        urllib.request.urlretrieve(file_url, tmp_file)
        print('file url ', url)
        # files = {'file': open(file, 'rb')}
        file_name = file.filename
        print('filename is ', file, file_name)
        file_path = os.path.abspath(('./static/'))
        print(file_path)
        with open('test', "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            shutil.copyfile('test', file_path + '/' + file_name)
            # shutil.copyfile('test', file_path + '/' + image_id)
            if not os.path.exists(file_path + 'test'):
            # if not os.path.exists(file_path + image_id):
                print('yes there is a file')
                os.remove(file_path + '/' + 'test')
                # os.remove(file_path + '/' + image_id)
                shutil.move('test', file_path)
                # shutil.move(image_id, file_path)
            else:
                shutil.move('test', file_path)
                # shutil.move(image_id, file_path)
        print('before opening the file')
        with open(file_path + '/' + file_name, 'rb') as a_file:
            print('printing file name ', a_file)
            file_dict = {"file_to_upload.txt": a_file}
            file_upload_response = requests.post(url, files=file_dict)
            print('file_upload_response ', file_upload_response.status_code)
            print('file_upload_response ', file_upload_response.content)


            # Fake Response for file upload
            # file_upload_response = sanction_file_upload_response1
            print(file_upload_response['status_code'])
            if(file_upload_response['status_code']!=200):
                log_id = await insert_logs('NAC', 'FUNCTION', 'sanction_fileupload', '403', 'File upload forbidden',
                                           datetime.now())

                result = JSONResponse(status_code=403, content={"message": f"File upload forbidden, "})
            else:
                store_record_time = datetime.now()
                file_upload_info = {
                    'customer_id': customer_id,
                    'file_name': file_name,
                    "message": f"File Replaced Successfully : {file_type}",
                    'status': 'SUCCESS',
                    'created_date': store_record_time
                }
                insert_query = sanction_fileupload.insert().values(file_upload_info)
                file_upload_id = await database.execute(insert_query)
                print('query', insert_query)
        # str_url = str(url)
        # str_data = data.dict()
        log_id = await insert_logs(str(url), 'NAC', str(file_dict), file_upload_response.status_code,
                                   file_upload_response.content, datetime.now())
        result = {"customer_id": customer_id, "file_size": file, "choice": file_type}
    except Exception as e:
        result = JSONResponse(status_code=500, content={"message": f"Error Occurred at Northern Arc Post Method - {e.args[0]}"})
        print(e.args[0])
    return result


@router.get("/sanction-status", tags=["Sanction"])
async def sanction_status(
        customer_id: str, database: Database = Depends(get_database)
):
    try:
        get_sanction_response = await nac_get_sanction('status', customer_id)
        get_sanction_response_status = hanlde_response_status(get_sanction_response)
        get_sanction_response_body = hanlde_response_body(get_sanction_response)
        if(get_sanction_response_status == 200):
            print('FOUND CUSTOMER IN NAC', get_sanction_response_body)
            result = JSONResponse(status_code=500, content=get_sanction_response_body)
        else:
            print('FOUND CUSTOMER IN NAC', get_sanction_response_body)
            result = JSONResponse(status_code=500, content=get_sanction_response_body)
    except Exception as e:
        logger.exception(f"{datetime.now()} - Issue with create_sanction function, {e.args[0]}")
        result = JSONResponse(status_code=500,
                              content={"message": f"Error Occurred at Northern Arc Post Method - {e.args[0]}"})
    return result


async def find_loan_id_from_sanction(
        customer_id
):
    try:
        database = get_database()
        select_query = sanction.select().where(sanction.c.customer_id == customer_id).order_by(sanction.c.id.desc())
        print('raw_sanction', select_query)
        raw_sanction = await database.fetch_one(select_query)

        sanction_dict = {
            "loanID": raw_sanction[61]
        }
        print( '*********************************** SUCCESSFULLY FETCHED LOAN ID BY SANCTION REF ID FROM DB  ***********************************')
        result = JSONResponse(status_code=200, content=sanction_dict)
    except Exception as e:
        logger.exception(f"{datetime.now()} - Issue with find_dedupe function, {e.args[0]}")
        print(
            '*********************************** FAILURE FETCHING SANCTION REFERENCE ID FROM DB  ***********************************')
        db_log_error = {"error": 'DB', "error_description": 'Customer ID not found in DB'}
        result = JSONResponse(status_code=500, content=db_log_error)
    return result


@router.get("/download-upload-loan-document",  tags=["Sanction"])
async def download_and_upload_file(customer_id, document_id):
    try:
        download_file_from_stream_response = await download_file_from_stream(document_id)
        download_file_from_stream_response_status = hanlde_response_status(download_file_from_stream_response)
        download_file_from_stream_response_body = hanlde_response_body(download_file_from_stream_response)
        if(download_file_from_stream_response_status == 200):
            print('printing heijdsljlsadfjljdsa', download_file_from_stream_response_status, download_file_from_stream_response_body)
            file_to_upload = download_file_from_stream_response_body.get('filename')
            print('BEFORE SNEDING ', file_to_upload)
            upload_file = await upload_file_to_nac('uploadFile', file_to_upload, 'AADHAR_DOC', customer_id)
            upload_file_status = hanlde_response_status(upload_file)
            upload_file_body = hanlde_response_body(upload_file)
            if(upload_file.status_code == 200):

                print('SUCCESS UPLOADING ', upload_file)
                # result = JSONResponse(status_code=200, content=download_file_from_stream_response)
                result = JSONResponse(status_code=200, content=upload_file_body)
            else:
                print('FAILED UPLOADING ', upload_file)
                result = JSONResponse(status_code=404, content=upload_file_body)
        else:
            logger.exception(f"{datetime.now()} - Issue with download_and_upload_file function  {download_file_from_stream_response_body}")
            result = JSONResponse(status_code=404, content=download_file_from_stream_response_body)
    except Exception as e:
        logger.exception(f"{datetime.now()} - Issue with download_and_upload_file function, {e.args[0]}")
        print('***** FAILURE DOWNLOADING FILE FROM PERDIX  *****')
        db_log_error = {"error": 'DB', "error_description": 'Problem with NAC endpoint'}
        result = JSONResponse(status_code=500, content=db_log_error)
    return result


