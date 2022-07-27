from datetime import datetime
from typing import Optional, List, Union

import sqlalchemy
from pydantic import BaseModel, Field
from sqlalchemy.dialects.mysql import LONGTEXT


class CollectBase(BaseModel):
    demandAmount: Optional[int] = 1000
    demandDate: Optional[str] = "2021-11-05"
    partnerLoandId: Optional[str] = "2048290"
    reference: Optional[str] =  "UTRNUMBER"
    repaymentAmount: Optional[int] = 1000
    repaymentDate: Optional[str] = "2021-11-05"
    settlementDate: Optional[str] = "2021-11-05"
    tdsAmount: Optional[int] = 100
    outstandingAmount: Optional[int] = 100


class CreateCollect(CollectBase):
    pass


class CollectDB(CollectBase):
    id: int


collect_metadata = sqlalchemy.MetaData()


collect = sqlalchemy.Table(
    "collect",
    collect_metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("demand_amount", sqlalchemy.Integer, nullable=True),
    sqlalchemy.Column("demand_date", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("instrument_type", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("partner_loan_id", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("reference", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("repayment_amount", sqlalchemy.Integer, nullable=True),
    sqlalchemy.Column("repayment_date", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("settlement_date", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("tds_amount", sqlalchemy.Integer, nullable=True),
    sqlalchemy.Column("outstanding_amount", sqlalchemy.Integer, nullable=True),
    sqlalchemy.Column("transaction_name", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("created_date", sqlalchemy.DateTime(), nullable=True),
)