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
from dm_nac_service.resource.log_config import logger
from dm_nac_service.resource.generics import handle_none, hanlde_response_body, hanlde_response_status

from dm_nac_service.app_responses.disbursement import disbursement_request_success_response, disbursement_request_error_response1, disbursement_request_error_response2, disbursement_request_error_response3, disbursement_status_success_response1, disbursement_status_success_response2, disbursement_status_error_response1, disbursement_status_error_response2, disbursement_status_error_response3


from dm_nac_service.data.disbursement_model import (
    disbursement,
    DisbursementBase,
    DisbursementDB,
    CreateDisbursement
)

from dm_nac_service.data.sanction_model import (
sanction
)

router = APIRouter()


@router.post("/find-customer-sanction", tags=["Sanction"])
async def find_customer_sanction(
        loan_id
):
    try:
        database = get_database()
        select_query = sanction.select().where(sanction.c.loan_id == loan_id).order_by(sanction.c.id.desc())
        raw_sanction = await database.fetch_one(select_query)
        sanction_dict = {
            "customerId": raw_sanction[1],
            "sanctionRefId": raw_sanction[2]
        }
        print(
            '*********************************** SUCCESSFULLY FETCHED SANCTION REFERENCE ID FROM DB  ***********************************')
        result = JSONResponse(status_code=200, content=sanction_dict)
    except Exception as e:
        logger.exception(f"{datetime.now()} - Issue with find_dedupe function, {e.args[0]}")
        print(
            '*********************************** FAILURE FETCHING SANCTION REFERENCE ID FROM DB  ***********************************')
        db_log_error = {"error": 'DB', "error_description": 'Dedupe Reference ID not found in DB'}
        result = JSONResponse(status_code=500, content=db_log_error)
    return result


@router.post("/disbursement", tags=["Disbursement"])
async def create_disbursement(
    # disbursement_data: CreateDisbursement,
    disbursement_data
    # database: Database = Depends(get_database)
):
    try:
        database = get_database()
        # disbursement_data_dict = disbursement_data.dict()

        disbursement_data_dict = disbursement_data
        # print('printing the disbursment', disbursement_data)


        disbursement_response = await nac_disbursement('disbursement', disbursement_data_dict)
        print('BEFORE response from disburmsent info', disbursement_response)
        disbursement_response_status = hanlde_response_status(disbursement_response)
        disbursement_response_body = hanlde_response_body(disbursement_response)

        disbursement_response_content_status = disbursement_response_body['content']['status']
        disbursement_response_message = disbursement_response_body['content']['message']
        logger.info(f"INSDIE CREATE DISBURSEMEN {disbursement_response_content_status} {disbursement_response_body}")
        print('AFTER response from disburmsent info', disbursement_response_body)
        if(disbursement_response_status == 200):
            print('1 -AFTER AFTER response from disburmsent info')
            # sanction_reference_id = disbursement_response_body['content']['value']['disbursementReferenceId']
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
            print('2 -AFTER AFTER response from disburmsent info', disbursement_info)
            disbursement_info['message'] = disbursement_response_message
            disbursement_info['status'] = disbursement_response_content_status
            disbursement_info['disbursement_reference_id'] = disbursement_response_body['content']['value']['disbursementReferenceId']
            insert_query = disbursement.insert().values(disbursement_info)
            disbursement_id = await database.execute(insert_query)
            result = JSONResponse(status_code=200, content=disbursement_response_body)
            print('SUCCESSFULLY COMING OUT OF CREATE DISBURSEMENT ', result)
        else:
            logger.info(f"FAILED INSDIE CREATE DISBURSEMEN {disbursement_response_content_status} {disbursement_response_message}")
            result = JSONResponse(status_code=500, content=disbursement_response_body)
            print('RESULT IN CREATE DISUB', result)
    except Exception as e:
        logger.exception(f"{datetime.now()} - Issue with find_dedupe function, {e.args[0]}")
        result = JSONResponse(status_code=500, content={"message": f"Issue with Northern Arc API, {e.args[0]}"})
    return result
