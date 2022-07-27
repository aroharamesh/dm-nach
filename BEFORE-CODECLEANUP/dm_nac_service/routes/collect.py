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


from dm_nac_service.gateway.nac_collect import nac_collect
from dm_nac_service.data.database import get_database, sqlalchemy_engine, insert_logs

from dm_nac_service.app_responses.collect import collect_request, collect_response


from dm_nac_service.data.collect_model import (
    collect,
    CollectDB,
    CollectBase,
    CreateCollect
)

router = APIRouter()

TRANSACTION_NAMES = ['Advance Repayment', 'Overdue-Payment', 'Pre-payment', 'Scheduled Demand', 'Fee Payment', 'Scheduled-Payment', 'Pre-Closure']

INSTRUMENT_TYPES = ['UPI', 'CASH', 'CASH_PAID_ON_DELIVERY', 'CASHBACK', 'DEBIT_CARD', 'DISPUTE', 'NEFT', 'IMPS', 'NACH', 'NEFT_RTGS', 'NETBANKING', 'REFUND', 'SHIPMENT', 'CHEQUE', 'EARLY_PAY_DISCOUNT']

@router.post("/collect", tags=["Collect"])
async def create_collect(
    collect_data: CreateCollect, transaction_name: str = Query("Transaction Names", enum=TRANSACTION_NAMES), instrument_types: str = Query("Instrument Types", enum=INSTRUMENT_TYPES), database: Database = Depends(get_database)
):
    try:
        collect_data_dict = collect_data.dict()
        store_record_time = datetime.now()
        collect_info = {
            'demand_amount': collect_data_dict['demandAmount'],
            'demand_date': collect_data_dict['demandDate'],
            'partner_loan_id': collect_data_dict['partnerLoandId'],
            'reference': collect_data_dict['reference'],
            'repayment_amount': collect_data_dict['repaymentAmount'],
            'repayment_date': collect_data_dict['repaymentDate'],
            'settlement_date': collect_data_dict['settlementDate'],
            'tds_amount': collect_data_dict['tdsAmount'],
            'outstanding_amount': collect_data_dict['outstandingAmount'],
            'transaction_name': transaction_name,
            'instrument_type': instrument_types,
            'created_date': store_record_time
        }
        collect_response = await nac_collect('collection', 'CIN1234', collect_data)

        print('printing collect information fro response', collect_response.status_code,collect_response.content )

        insert_query = collect.insert().values(collect_info)
        collect_id = await database.execute(insert_query)
        result = collect_info
    except Exception as e:
        log_id = await insert_logs('MYSQL', 'DB', 'create_collect', '500', 'Error Occurred at DB level',
                                   datetime.now())
        result = JSONResponse(status_code=500, content={"message": f"Issue with Northern Arc API, {e.args[0]}"})
    return result
