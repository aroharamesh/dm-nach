import uvicorn
# import logging
# from logging.config import dictConfig
# from dm_nac_service.resource.log_config import LogConfig
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi_utils.tasks import repeat_every
# Data
from dm_nac_service.data.database import get_database, sqlalchemy_engine
from dm_nac_service.data.dedupe_model import dedupe_metadata
from dm_nac_service.data.sanction_model import (sanction_metadata)
from dm_nac_service.data.disbursement_model import disbursement_metadata
from dm_nac_service.data.collect_model import collect_metadata
from dm_nac_service.resource.log_config import logger

# Router
from dm_nac_service.data.logs_model import (logs_metadata)
from dm_nac_service.routes.dedupe import router as dedupte_router
from dm_nac_service.routes.sanction import router as sanction_router
from dm_nac_service.routes.disbursement import router as disbursement_router
from dm_nac_service.routes.collect import router as collect_router
from dm_nac_service.routes.perdix_automator import router as perdix_router, update_sanction_in_db
from dm_nac_service.commons import get_env_or_fail

origins = ["*"]

# Adding the logger and log file
# dictConfig(LogConfig().dict())
# logger = logging.getLogger("dm-nac-service")
# logfile_handler = logging.FileHandler("dm_nac_service/logs/server.log")
# logger.addHandler(logfile_handler)

app = FastAPI(title="DM-NAC",
              debug=True,
    description='Dvara Money NAC Integration',
    version="0.0.1",
    terms_of_service="http://dvara.com/terms/",
    contact={
        "name": "DM - NAC Integration",
        "url": "http://x-force.example.com/contact/",
        "email": "contact@dvara.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SCHEDULER_TIME = 'scheduler-time'

scheduler_start_in_seconds = get_env_or_fail(SCHEDULER_TIME, 'start-seconds', SCHEDULER_TIME + ' start-seconds not configured')
scheduler_end_in_seconds = get_env_or_fail(SCHEDULER_TIME, 'end-seconds', SCHEDULER_TIME + ' end-seconds not configured')

@app.on_event("startup")
async def startup():
    await get_database().connect()
    # metadata.create_all(sqlalchemy_engine)
    dedupe_metadata.create_all(sqlalchemy_engine)
    logs_metadata.create_all(sqlalchemy_engine)
    sanction_metadata.create_all(sqlalchemy_engine)
    disbursement_metadata.create_all(sqlalchemy_engine)
    collect_metadata.create_all(sqlalchemy_engine)


@app.on_event("startup")
@repeat_every(seconds=int(scheduler_start_in_seconds) * int(scheduler_end_in_seconds))  # 1 minute
async def update_mandate_task() -> str:
    # update_mandate_status = await pending_mandate_status('fake-super-secret-token')
    # update_sanction_status = await update_sanction_in_db()
    logger.info('Hello from logger')
    print("Hello World every 5 minutes")
    return "Hello World"

@app.on_event("shutdown")
async def shutdown():
    await get_database().disconnect()


app.include_router(dedupte_router, prefix="")
app.include_router(sanction_router, prefix="")
app.include_router(disbursement_router, prefix="")
app.include_router(collect_router, prefix="")
app.include_router(perdix_router, prefix="")



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8008)


# uvicorn example:app --log-config /path/to/log.ini