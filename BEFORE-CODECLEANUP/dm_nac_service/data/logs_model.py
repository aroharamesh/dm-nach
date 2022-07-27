from datetime import datetime
from typing import Optional
from sqlalchemy.dialects.mysql import LONGTEXT

import sqlalchemy
from pydantic import BaseModel, Field


class LogsBase(BaseModel):
    request_str: str
    response_str: str
    created_date: datetime = Field(default_factory=datetime.now)


class LogsCreate(LogsBase):
    pass


class logsDB(LogsBase):
    id: int


logs_metadata = sqlalchemy.MetaData()


applogs = sqlalchemy.Table(
    "applogs",
    logs_metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("app_type", sqlalchemy.String(length=255), nullable=True),
    sqlalchemy.Column("request_type", sqlalchemy.String(length=255), nullable=True),
    sqlalchemy.Column("request", sqlalchemy.String(length=2000), nullable=True),
    sqlalchemy.Column("request_json", sqlalchemy.String(length=2000), nullable=True),
    sqlalchemy.Column("response_status", sqlalchemy.String(length=255), nullable=True),
    sqlalchemy.Column("response_content", sqlalchemy.String(length=2000), nullable=True),
    sqlalchemy.Column("created_date", sqlalchemy.DateTime(), nullable=True)
)