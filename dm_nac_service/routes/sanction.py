from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from datetime import datetime
from databases import Database
from fastapi.exceptions import HTTPException

from dm_nac_service.data.database import get_database, sqlalchemy_engine, insert_logs
from dm_nac_service.gateway.nac_dedupe import nac_dedupe
from dm_nac_service.data.sanction_model import (
    SanctionDB,
    SanctionBase,
    CreateSanction,
    sanction

)

router = APIRouter()


@router.post("/sanction", response_model=SanctionDB, tags=["Sanction"])
async def create_sanction(
    sanction_data: CreateSanction, database: Database = Depends(get_database)
) -> SanctionDB:
    try:
        print('prepared data from create_sanction', sanction_data.dict())
        result = {"result": "testing"}
    except Exception as e:
        result = {"error": "500 Internal Error"}
        raise HTTPException(status_code=500, detail=f"Issue with Northern Arc API, {e.args[0]}")
        print(e.args[0])
    return result