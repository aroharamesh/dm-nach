import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Data
from dm_nac_service.data.database import get_database, sqlalchemy_engine
from dm_nac_service.data.dedupe_model import dedupe_metadata
from dm_nac_service.data.sanction_model import (sanction_metadata)
from dm_nac_service.data.disbursement_model import disbursement_metadata
from dm_nac_service.data.collect_model import collect_metadata

# Router
from dm_nac_service.data.logs_model import (logs_metadata)
from dm_nac_service.routes.dedupe import router as dedupte_router
from dm_nac_service.routes.sanction import router as sanction_router
from dm_nac_service.routes.disbursement import router as disbursement_router
from dm_nac_service.routes.collect import router as collect_router


origins = ["*"]


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


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await get_database().connect()
    # metadata.create_all(sqlalchemy_engine)
    dedupe_metadata.create_all(sqlalchemy_engine)
    logs_metadata.create_all(sqlalchemy_engine)
    sanction_metadata.create_all(sqlalchemy_engine)
    disbursement_metadata.create_all(sqlalchemy_engine)
    collect_metadata.create_all(sqlalchemy_engine)



@app.on_event("shutdown")
async def shutdown():
    await get_database().disconnect()

@app.get("/")
async def root():
    return {"message": "Hello World"}


app.include_router(dedupte_router, prefix="")
app.include_router(sanction_router, prefix="")
app.include_router(disbursement_router, prefix="")
app.include_router(collect_router, prefix="")

@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8008)