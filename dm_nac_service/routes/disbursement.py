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


from dm_nac_service.gateway.nac_disbursement import nac_disbursement, disbursement_get_status
from dm_nac_service.data.database import get_database, sqlalchemy_engine, insert_logs

from dm_nac_service.app_responses.disbursement import disbursement_request_success_response, disbursement_request_error_response1, disbursement_request_error_response2, disbursement_request_error_response3, disbursement_status_success_response1, disbursement_status_success_response2, disbursement_status_error_response1, disbursement_status_error_response2, disbursement_status_error_response3


from dm_nac_service.data.disbursement_model import (
    disbursement,
    DisbursementBase,
    DisbursementDB,
    CreateDisbursement
)

router = APIRouter()


async def get_sanction_or_404(
    sanction_reference_id: int
) -> DisbursementDB:
    database = get_database()
    # print('getting inside get_disbursement_or_404')
    select_query = disbursement.select().where(disbursement.c.sanction_reference_id == sanction_reference_id)
    # print('printing the sql query ', select_query)
    raw_disbursement = await database.fetch_one(select_query)
    # print(raw_disbursement)

    if raw_disbursement is None:
        return None

    return DisbursementDB(**raw_disbursement)


async def get_disbursement_or_404(
    disbursement_reference_id: int
) -> DisbursementDB:
    database = get_database()
    # print('getting inside get_disbursement_or_404')
    select_query = disbursement.select().where(disbursement.c.disbursement_reference_id == disbursement_reference_id)
    # print('printing the sql query ', select_query)
    raw_disbursement = await database.fetch_one(select_query)
    # print(raw_disbursement)

    if raw_disbursement is None:
        return None

    return DisbursementDB(**raw_disbursement)


@router.post("/disbursement", tags=["Disbursement"])
async def create_disbursement(
    disbursement_data: CreateDisbursement, database: Database = Depends(get_database)
):
    try:
        disbursement_data_dict = disbursement_data.dict()
        # print('printing the disbursment', disbursement_data)
        sanction_reference_id = disbursement_data_dict['sanctionReferenceId']

        disbursement_response = await nac_disbursement('disbursement', disbursement_data_dict)

        disbursement_response_status = disbursement_response['content']['status']
        disbursement_response_message = disbursement_response['content']['message']
        store_record_time = datetime.now()
        disbursement_info = {
            'customer_id': disbursement_data_dict['customerId'],
            'originator_id': disbursement_data_dict['originatorId'],
            'sanction_reference_id': disbursement_data_dict['sanctionReferenceId'],
            'requested_amount': disbursement_data_dict['requestedAmount'],
            'ifsc_code': disbursement_data_dict['ifscCode'],
            'branch_name': disbursement_data_dict['branchName'],
            'processing_fees': disbursement_data_dict['processingFees'],
            'insurance_amount': disbursement_data_dict['insuranceAmount'],
            'disbursement_date': disbursement_data_dict['disbursementDate'],
            'created_date': store_record_time,
        }
        disbursement_response_status = disbursement_response['content']['status']
        if(disbursement_response_status == 'SUCCESS'):
            disbursement_info['message'] = disbursement_response_message
            disbursement_info['status'] = disbursement_response_status
            disbursement_info['disbursement_reference_id'] = disbursement_response['content']['value']['disbursementReferenceId']
        else:
            disbursement_info['message'] = disbursement_response_message
            disbursement_info['status'] = disbursement_response_status

        get_sanction_from_db = await get_sanction_or_404(sanction_reference_id)
        # print('get_disbursement_from_db', get_disbursement_from_db)

        if(get_sanction_from_db is None):
            insert_query = disbursement.insert().values(disbursement_info)
            # print('query', insert_query)
            disbursement_id = await database.execute(insert_query)
        else:
            result = JSONResponse(status_code=500, content={"message": f"{sanction_reference_id} is already present"})

        result = disbursement_response
    except Exception as e:
        log_id = await insert_logs('MYSQL', 'DB', 'NA', '500', 'Error Occurred at DB level',
                                   datetime.now())
        result = JSONResponse(status_code=500, content={"message": f"Issue with Northern Arc API, {e.args[0]}"})
    return result


@router.get("/disbursement-status", tags=["Disbursement"])
async def get_disbursement_status(
    disbursement_reference_id: int, database: Database = Depends(get_database)
):
    try:
        print('coming inside of disbursement status', disbursement_reference_id)
        get_disbursement_from_db = await get_disbursement_or_404(disbursement_reference_id)

        print('printing get_disbursement_from_db', get_disbursement_from_db)
        disbursement_status_response = await disbursement_get_status('disbursement', disbursement_reference_id)
        if(get_disbursement_from_db is not None):
            print('get_disbursement_from_db')
            disbursement_status_response_error = disbursement_status_response.get('error')
            if(not disbursement_status_response_error):
                print('disbursement_status_response_error')
                disbursement_status_response_status = disbursement_status_response['content']['status']
                if(disbursement_status_response_status=='SUCCESS'):
                    print('disbursement_status_response_status')
                    disbursement_status_response_stage = disbursement_status_response['content']['value']['stage']
                    disbursement_status_response_dis_status = disbursement_status_response['content']['value']['disbursementStatus']
                    disbursement_status_response_utr = disbursement_status_response.get('content').get('value').get('utr')
                    if(not disbursement_status_response_utr):
                        query = disbursement.update().where(disbursement.c.disbursement_reference_id == disbursement_reference_id).values(
                                                                                                             disbursement_status=disbursement_status_response_dis_status,
                                                                                                             stage=disbursement_status_response_stage,
                                                                                                            status="",
                                                                                                            message="")
                        customer_updated = await database.execute(query)
                    else:
                        query = disbursement.update().where(
                            disbursement.c.disbursement_reference_id == disbursement_reference_id).values(
                            utr=disbursement_status_response_utr,
                            disbursement_status=disbursement_status_response_dis_status,
                            stage=disbursement_status_response_stage)
                        customer_updated = await database.execute(query)
                else:
                    print('else disbursement_status_response_status error')
                    disbursement_status_response_message = disbursement_status_response.get('content').get('message')
                    if(not disbursement_status_response_message):
                        print('not disbursement_status_response_message')
                        disbursement_status_response_stage = disbursement_status_response.get('content').get('value').get('stage')
                        disbursement_status_response_status = disbursement_status_response.get('content').get('value').get('status')
                        query = disbursement.update().where(
                            disbursement.c.disbursement_reference_id == disbursement_reference_id).values(
                            stage=disbursement_status_response_stage,
                        disbursement_status =disbursement_status_response_status)
                        customer_updated = await database.execute(query)
                    else:
                        print('message not found')
            else:

                disbursement_status_response_status = disbursement_status_response['status']
                disbursement_status_response_message = disbursement_status_response['error']
                query = disbursement.update().where(
                    disbursement.c.disbursement_reference_id == disbursement_reference_id).values(
                    message=disbursement_status_response_message,
                    status=disbursement_status_response_status)
                customer_updated = await database.execute(query)


        # print('get_disbursement_status ', get_disbursement_status)

        result = disbursement_status_response
    except Exception as e:
        log_id = await insert_logs('MYSQL', 'DB', 'NA', '500', 'Error Occurred at DB level',
                                   datetime.now())
        result = JSONResponse(status_code=500, content={"message": f"Issue with Northern Arc API, {e.args[0]}"})
    return result