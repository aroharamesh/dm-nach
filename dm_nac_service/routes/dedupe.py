from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from datetime import datetime
from databases import Database
from fastapi.exceptions import HTTPException

from dm_nac_service.data.database import get_database, sqlalchemy_engine, insert_logs
from dm_nac_service.gateway.nac_dedupe import nac_dedupe
from dm_nac_service.app_responses.dedupe import dedupe_response_data
from dm_nac_service.data.dedupe_model import (
    DedupeDB,
    DedupeCreate,
    dedupe

)


router = APIRouter()


@router.post("/dedupe", response_model=DedupeDB, tags=["Dedupe"])
async def create_dedupe(
    dedupe_data: DedupeCreate, database: Database = Depends(get_database)
) -> DedupeDB:
    try:
        # print('prepared data from create_dedupe', dedupe_data.dict())
        dedupe_dict = dedupe_data.dict()
        dedupe_get_root = dedupe_dict.get('__root__')
        # print('dedupe source - ', dedupe_get_root)
        # Real API response after passing the dedupe data
        dedupe_response = await nac_dedupe('dedupe', dedupe_data)
        store_record_time = datetime.now()
        dedupe_response_id = str(dedupe_response['dedupeReferenceId'])
        # print('before dedupe_info', dedupe_response['dedupeRequestSource']['dateOfBirth'])
        dedupue_info = {
            'dedupe_reference_id': dedupe_response_id,
            'account_number': dedupe_response['dedupeRequestSource']['accountNumber'],
            'contact_number': dedupe_response['dedupeRequestSource']['contactNumber'],
            'customer_name': dedupe_response['dedupeRequestSource']['customerName'],
            'dob': dedupe_response['dedupeRequestSource']['dateOfBirth'],
            'loan_id': dedupe_response['dedupeRequestSource']['loanId'],
            'pincode': dedupe_response['dedupeRequestSource']['pincode'],
            'response_type': dedupe_response['type'],
            'dedupe_present': str(dedupe_response['isDedupePresent']),
            'id_type1': dedupe_response['dedupeRequestSource']['kycDetailsList'][0]['type'],
            'id_value1': dedupe_response['dedupeRequestSource']['kycDetailsList'][0]['value'],
            'id_type2': dedupe_response['dedupeRequestSource']['kycDetailsList'][1]['type'],
            'id_value2': dedupe_response['dedupeRequestSource']['kycDetailsList'][1]['value'],
            'created_date': store_record_time,
        }
        # print('dedupue_info',  dedupue_info)
        insert_query = dedupe.insert().values(dedupue_info)
        # print('query', insert_query)
        dedupe_id = await database.execute(insert_query)
        result = JSONResponse(status_code=200, content=dedupe_response)

        # Fake API response from pdf file
        # dedupe_response = dedupe_response_data
        # print('Fake API response from pdf file ', dedupe_response)
        # store_record_time = datetime.now()
        # dedupue_info = {
        #     'dedupe_reference_id': dedupe_response[0]['dedupeReferenceId'],
        #     'originator_id': dedupe_response[0]['referenceLoan']['originatorId'],
        #     'account_number': dedupe_get_root[0]['accountNumber'],
        #     'contact_number': dedupe_get_root[0]['contactNumber'],
        #     'customer_name': dedupe_get_root[0]['customerName'],
        #     'dob': dedupe_get_root[0]['dateofBirth'],
        #     'id_type': dedupe_get_root[0]['kycDetailsList'][0]['type'],
        #     'id_value': dedupe_get_root[0]['kycDetailsList'][0]['value'],
        #     'loan_id': dedupe_get_root[0]['loanId'],
        #     'pincode': dedupe_get_root[0]['pincode'],
        #     'created_date': store_record_time,
        # }
        #
        # print('dedupe_info', dedupue_info)
        # insert_query = dedupe.insert().values(dedupue_info)
        # print('query', insert_query)
        # dedupe_id = await database.execute(insert_query)
        # result = JSONResponse(status_code=200, content={"dedupeReferenceId": dedupe_response})
    except Exception as e:
        log_id = await insert_logs('MYSQL', 'DB', 'NA', '500', {e.args[0]},
                                   datetime.now())
        result = JSONResponse(status_code=500, content={"message": f"Issue with Northern Arc API, {e.args[0]}"})
    return result