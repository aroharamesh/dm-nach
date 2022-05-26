from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from datetime import datetime
from databases import Database
from fastapi.exceptions import HTTPException

from dm_nac_service.data.database import get_database, sqlalchemy_engine, insert_logs
from dm_nac_service.gateway.nac_dedupe import nac_dedupe
from dm_nac_service.data.dedupe_model import (
    DedupeDB2,
    DedupeBase,
    DedupeCreate,
    dedupe

)


router = APIRouter()


@router.post("/dedupe", response_model=DedupeDB2, tags=["Dedupe"])
async def create_dedupe(
    dedupe_data: DedupeCreate, database: Database = Depends(get_database)
) -> DedupeDB2:
    try:
        print('prepared data from create_dedupe', dedupe_data.dict())
        dedupe_response = await nac_dedupe('dedupe', dedupe_data)
        print('dedupe reference id after', dedupe_response)
        store_record_time = datetime.now()
        dedupue_info = {
            'dedupe_reference_id': str(dedupe_response),
            'created_date': store_record_time,
            'id_type': 'test'
        }
        print('dedupe_info', dedupue_info)
        insert_query = dedupe.insert().values(dedupue_info)
        print('query', insert_query)
        dedupe_id = await database.execute(insert_query)
        result = {"dedupeReferenceId": dedupe_response}

    except Exception as e:
        result = {"error": "500 Internal Error"}
        raise HTTPException(status_code=500, detail=f"Issue with Northern Arc API, {e.args[0]}")
        print(e.args[0])
    return result