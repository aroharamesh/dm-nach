import random
import re
import shutil

import requests
import os

from fastapi import APIRouter, Depends, status, File, UploadFile, Form, Query
from fastapi.responses import JSONResponse
from datetime import datetime
from databases import Database
from fastapi.exceptions import HTTPException

from dm_nac_service.commons import get_env_or_fail
from dm_nac_service.data.database import get_database, sqlalchemy_engine, insert_logs
from dm_nac_service.gateway.nac_sanction import nac_sanction, nac_sanction_fileupload, nac_get_sanction
from dm_nac_service.app_responses.sanction import sanction_request_data, sanction_response_success_data, sanction_response_error_data
from dm_nac_service.data.dedupe_model import (
    dedupe
)
from dm_nac_service.resource.generics import response_to_dict
from dm_nac_service.data.sanction_model import (
    SanctionDB,
    SanctionBase,
    CreateSanction,
    sanction,
    FileChoices,
    sanction_fileupload
)

NAC_SERVER = 'northernarc-server'

FILE_CHOICES = ['SELFIE', 'AADHAR_XML', 'MITC', 'VOTER_CARD', 'DRIVING_LICENSE', 'SANCTION_LETTER', 'PAN', 'PASSPORT', 'AADHAR_DOC', 'LOAN_APPLICATION', 'LOAN_AGREEMENT']

router = APIRouter()


@router.post("/sanction", response_model=SanctionDB, tags=["Sanction"])
async def create_sanction(
    sanction_data: CreateSanction, database: Database = Depends(get_database)
) -> SanctionDB:
    try:
        print('prepared data from create_sanction', sanction_data.dict())
        sanction_dict = sanction_data.dict()
        # Real API response from NAC
        sanction_response = await nac_sanction('uploadSanctionJSON', sanction_dict)
        print('sanction response from create sanction', sanction_response)
        get_sanction_response = sanction_response.get('error')
        if(sanction_response['content']['status'] == 'SUCCESS'):
            customer_id = sanction_response['content']['value']['customerId']
            store_record_time = datetime.now()
            sanction_info = {
                'customer_id': customer_id,
                'created_date': store_record_time,
            }
            insert_query = sanction.insert().values(sanction_info)
            print('query', insert_query)
            sanction_id = await database.execute(insert_query)
            result = JSONResponse(status_code=200, content={"customerid": sanction_response})
            return result

            # result = sanction_info
        else:
            log_id = await insert_logs('create_sanction', 'NAC', sanction_response['content']['status'], '500', sanction_response['content']['message'],
                                       datetime.now())
            result = JSONResponse(status_code=500, content={"message": f"Issue with Northern Arc API"})



        # Fake API response from pdf file
        # print('sanction dictionary', sanction_response)
        # For Success
        # sanction_response = sanction_response_success_data

        # For Error
        # sanction_response = sanction_response_error_data
        # store_record_time = datetime.now()
        #
        # if(sanction_response['content']['status'] == 'SUCCESS'):
        #     sanction_info = {
        #         'dedupe_reference_id': str(sanction_dict['dedupeReferenceId']),
        #         'customer_id': sanction_response['content']['customerId'],
        #         'client_id': sanction_response['content']['clientId'],
        #         'status': sanction_response['content']['status'],
        #         'created_date': store_record_time,
        #     }
        #     print('sanction_info', sanction_info)
        #     insert_query = sanction.insert().values(sanction_info)
        #     print('query', insert_query)
        #     dedupe_id = await database.execute(insert_query)
        #     result = JSONResponse(status_code=200, content={"result": "testing"})
        # else:
        #     log_id = await insert_logs('MYSQL', 'DB', sanction_response['content']['status'], '500', sanction_response['content']['message'],
        #                                datetime.now())
        #     result = JSONResponse(status_code=500, content={"message": f"Issue with Northern Arc API"})
    except Exception as e:
        log_id = await insert_logs('MYSQL', 'DB', 'NA', '500', 'Error Occurred at DB level',
                                   datetime.now())
        result = JSONResponse(status_code=500, content={"message": f"Issue with Northern Arc API, {e.args[0]}"})
    return result


@router.get("/deduperef", tags=["Sanction"])
async def find_deduperef(
    deduperef: str, database: Database = Depends(get_database)
):
    try:
        print('coming inside of find_deduperef')
        select_query = dedupe.select().where(dedupe.c.dedupe_reference_id == deduperef)
        raw_dedupe_ref = await database.fetch_one(select_query)
        print('dedupe ref ', raw_dedupe_ref)
        for i in raw_dedupe_ref:
            # if(i=='PANCARD'):
            #     i = i + 1
            #     pan_no = i
            #     print(pan_no)
            print(i)
        sanction_tuple = raw_dedupe_ref
        sanction_data = CreateSanction()
        #
        # testing = str(sanction_tuple[5])
        # ldat = re.findall('\d+-.\d+-.\d+', testing)
        # print('date in string', ldat[0])
        prepare_sanction_data = sanction_data.dict()
        prepare_sanction_data['mobile'] = sanction_tuple[3]
        prepare_sanction_data['firstName'] = sanction_tuple[4]
        prepare_sanction_data['pan'] = sanction_tuple[9]
        prepare_sanction_data['idProofNumberFromPartner'] = sanction_tuple[9]
        prepare_sanction_data['addressProofNumberFromPartner'] = sanction_tuple[7]
        prepare_sanction_data['dedupeReferenceId'] = sanction_tuple[1]
        prepare_sanction_data['primaryBankAccount'] = sanction_tuple[2]
        prepare_sanction_data['dob'] = sanction_tuple[5]
        prepare_sanction_data['currPincode'] = sanction_tuple[11]
        prepare_sanction_data['permPincode'] = sanction_tuple[11]
        prepare_sanction_data['loanId'] = sanction_tuple[10]
        prepare_sanction_data['clientId'] = "5c1d8168-ef34-41ed-ab23-aab" + str(random.randint(10, 10000))
        print('prepare_sanction_data - ', prepare_sanction_data)
        result = prepare_sanction_data
    except Exception as e:
        log_id = await insert_logs('MYSQL', 'FUNCTION', 'FIND_DEDUPEREF', '500', {e.args[0]},
                                   datetime.now())
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
        url = validate_url + f'/po/uploadFile?originatorId={originator_id}&fileType={file_type}&customerId={customer_id}'
        print('file url ', url)
        # files = {'file': open(file, 'rb')}
        file_name = file.filename
        print('filename is ', file, file_name)
        file_path = os.path.abspath(('./static/'))
        print(file_path)
        with open('test', "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            shutil.copyfile('test', file_path + '/' + file_name)
            if not os.path.exists(file_path + 'test'):
                print('yes there is a file')
                os.remove(file_path + '/' + 'test')
                shutil.move('test', file_path)
            else:
                shutil.move('test', file_path)
        with open(file_path + '/' + file_name, 'rb') as a_file:
            print('printing file name ', a_file)
            file_dict = {"file_to_upload.txt": a_file}
            file_upload_response = requests.post(url, files=file_dict)
            print('file_upload_response ', file_upload_response.status_code)
            print('file_upload_response ', file_upload_response.content)
            if(file_upload_response.status_code!=200):
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
        result = {"customer_id": customer_id, "file_size": file, "choice": file_type}
    except Exception as e:
        result = JSONResponse(status_code=500, content={"message": f"Error Occurred at Northern Arc Post Method - {e.args[0]}"})
        print(e.args[0])
    return result



@router.get("/sanction-status", tags=["Sanction"])
async def get_sanction(
        customer_id: str, database: Database = Depends(get_database)
):
    try:
        get_sanction_response = await nac_get_sanction('status', customer_id)
        status = get_sanction_response['content']['value']['status']
        stage = get_sanction_response['content']['value']['stage']
        rejectReason = get_sanction_response['content']['value']['rejectReason']
        bureauFetchStatus = get_sanction_response['content']['value']['bureauFetchStatus']
        select_query = sanction.select().where(sanction.c.customer_id == customer_id)
        raw_get_customer = await database.fetch_one(select_query)
        if raw_get_customer is None:
            return None
        else:
            query = sanction.update().where(sanction.c.customer_id == customer_id).values(status=status,
                                                                                                 stage=stage,
                                                                                                 reject_reason=rejectReason,
                                                                                                 bureau_fetch_status=bureauFetchStatus)
            customer_updated = await database.execute(query)
            return customer_updated
        print('get-sanction ', raw_get_customer)
        result = get_sanction_response
    except Exception as e:
        result = JSONResponse(status_code=500,
                              content={"message": f"Error Occurred at Northern Arc Post Method - {e.args[0]}"})
        print(e.args[0])
    return result