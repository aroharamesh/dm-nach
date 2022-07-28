import json
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from datetime import datetime
from dm_nac_service.resource.log_config import logger
from databases import Database
from fastapi.exceptions import HTTPException

from dm_nac_service.data.database import get_database, sqlalchemy_engine, insert_logs
from dm_nac_service.resource.generics import handle_none, hanlde_response_body, hanlde_response_status
from dm_nac_service.gateway.nac_dedupe import nac_dedupe
from dm_nac_service.app_responses.dedupe import dedupe_response_data
from dm_nac_service.data.dedupe_model import (
    DedupeDB,
    DedupeCreate,
    dedupe

)
# from dm_nac_service.routes.perdix_automator import update_loan


router = APIRouter()

@router.post("/dedupe", response_model=DedupeDB, tags=["Dedupe"])
async def find_dedupe(
        loan_id
) -> DedupeDB:
    try:
        # loan_id = 83748
        database = get_database()
        select_query = dedupe.select().where(dedupe.c.loan_id == loan_id).order_by(dedupe.c.id.desc())
        raw_dedupe = await database.fetch_one(select_query)
        dedupe_dict = {
            "dedupeRefId": raw_dedupe[1],
            "isDedupePresent": raw_dedupe[12],
            "isEligible": raw_dedupe[18],
            # "isEl1igible": "True",
            "message": raw_dedupe[19]
        }
        print( '*********************************** SUCCESSFULLY FETCHED DEDUPE REFERENCE ID FROM DB  ***********************************')
        result = JSONResponse(status_code=200, content=dedupe_dict)
    except Exception as e:
        logger.exception(f"{datetime.now()} - Issue with find_dedupe function, {e.args[0]}")
        print(
            '*********************************** FAILURE FETCHING DEDUPE REFERENCE ID FROM DB  ***********************************')
        db_log_error = {"error": 'DB', "error_description": 'Dedupe Reference ID not found in DB'}
        result = JSONResponse(status_code=500, content=db_log_error)
    return result


@router.post("/dedupe", response_model=DedupeDB, tags=["Dedupe"])
async def create_dedupe(
    # Below is to test this function manually
    # Data from model
    # dedupe_data: DedupeCreate,

    #  Data from automator
    automator_data,
    # database: Database = Depends(get_database)

) -> DedupeDB:
    try:
        database = get_database()

        print('2 - send data to gateway function  - ', automator_data)
        dedupe_response = await nac_dedupe('dedupe', automator_data)
        print('7 - Getting the dedupe reference from nac_dedupe function - ', dedupe_response)
        dedupe_response_decode_status = hanlde_response_status(dedupe_response)
        response_body_json = hanlde_response_body(dedupe_response)
        if(dedupe_response_decode_status == 200):

            store_record_time = datetime.now()
            dedupe_response_id = response_body_json.get('dedupeReferenceId')
            dedupe_response_id_str = str(dedupe_response_id)
            kycdetails_array = response_body_json.get('dedupeRequestSource').get('kycDetailsList')
            print('8 - Verify kycdetails_array', len(kycdetails_array))
            if (len(kycdetails_array) == 1):
                # For Real API
                print('9 - preparing  kycdetails_array to store in DB - ', dedupe_response)
                id_type1 = response_body_json.get('dedupeRequestSource').get('kycDetailsList')[0].get('type')
                id_value1 = response_body_json.get('dedupeRequestSource').get('kycDetailsList')[0].get('value')
                id_type2 = ""
                id_value2 = ""
            else:

                # For Real API
                id_type1 = response_body_json.get('dedupeRequestSource').get('kycDetailsList')[0].get('type')
                id_value1 = response_body_json.get('dedupeRequestSource').get('kycDetailsList')[0].get('value')
                id_type2 = response_body_json.get('dedupeRequestSource').get('kycDetailsList')[1].get('type')
                id_value2 = response_body_json.get('dedupeRequestSource').get('kycDetailsList')[1].get('value')
                print('9 - preparing  kycdetails_array to store in DB - ', dedupe_response)

            # For Real API
            loan_id = response_body_json.get('dedupeRequestSource').get('loanId')
            dedupe_response_result = len(response_body_json.get('results'))

            if (dedupe_response_result > 0):
                dedupue_info = {
                    'dedupe_reference_id': dedupe_response_id_str,
                    'account_number': response_body_json['dedupeRequestSource']['accountNumber'],
                    'contact_number': response_body_json['dedupeRequestSource']['contactNumber'],
                    'customer_name': response_body_json['dedupeRequestSource']['customerName'],
                    # 'dob': dedupe_response['dedupeRequestSource']['dateOfBirth'],
                    'loan_id': loan_id,
                    'pincode': response_body_json['dedupeRequestSource']['pincode'],
                    'response_type': response_body_json['type'],
                    'dedupe_present': str(response_body_json['isDedupePresent']),
                    'result_attribute': response_body_json['results'][0]['attribute'],
                    'result_value': response_body_json.get('results')[0].get('value', 'NA'),
                    # 'result_value': response_body_json['results'][0]['value'],
                    'result_rule_name': response_body_json['results'][0]['ruleName'],
                    'result_ref_loan_id': response_body_json['results'][0]['id'],
                    'result_is_eligible': response_body_json['results'][0]['isEligible'],
                    'result_message': response_body_json['results'][0]['message'],
                    'ref_originator_id': response_body_json['referenceLoan']['originatorId'],
                    'ref_sector_id': response_body_json['referenceLoan']['sectorId'],
                    'ref_max_dpd': response_body_json['referenceLoan']['maxDpd'],
                    'ref_first_name': response_body_json['referenceLoan']['firstName'],
                    'ref_date_of_birth': response_body_json['referenceLoan']['dateOfBirth'],
                    'ref_mobile_phone': response_body_json['referenceLoan']['mobilePhone'],
                    'ref_account_number_loan_ref': response_body_json['referenceLoan']['accountNumber'],
                    'id_type1': id_type1,
                    'id_value1': id_value1,
                    'id_type2': id_type2,
                    'id_value2': id_value2,
                    'created_date': store_record_time,
                }
            else:
                dedupue_info = {
                    'dedupe_reference_id': dedupe_response_id_str,
                    'account_number': response_body_json['dedupeRequestSource']['accountNumber'],
                    'contact_number': response_body_json['dedupeRequestSource']['contactNumber'],
                    'customer_name': response_body_json['dedupeRequestSource']['customerName'],
                    'dedupe_present': str(response_body_json['isDedupePresent']),
                    # 'dob': dedupe_response['dedupeRequestSource']['dateOfBirth'],
                    'loan_id': loan_id,
                    'pincode': response_body_json['dedupeRequestSource']['pincode'],
                    'response_type': response_body_json['type'],
                    'id_type1': id_type1,
                    'id_value1': id_value1,
                    'id_type2': id_type2,
                    'id_value2': id_value2,
                    'created_date': store_record_time,
                }
            print('10 - preparing Dedupe data to store in DB - ', dedupue_info)
            insert_query = dedupe.insert().values(dedupue_info)
            print('query', insert_query)
            dedupe_id = await database.execute(insert_query)
            print('11 - Response of the data after storing in DB - ', dedupe_id)
            result = JSONResponse(status_code=200, content=response_body_json)
        else:
            print('7b - failure generated dedupe ref id', )
            logger.exception(f"{datetime.now()} - Issue with create_dedupe function, {str(response_body_json)}")
            result = response_body_json
            print('error from create dedupe', result)

    except Exception as e:
        logger.exception(f"{datetime.now()} - Issue with create_dedupe function, {e.args[0]}")
        result = JSONResponse(status_code=500, content={"message": f"Issue with Northern Arc API, {e.args[0]}"})
    return result