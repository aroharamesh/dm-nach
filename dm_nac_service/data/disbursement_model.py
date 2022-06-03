from datetime import datetime
from typing import Optional, List, Union

import sqlalchemy
from pydantic import BaseModel, Field
from sqlalchemy.dialects.mysql import LONGTEXT


class DisbursementBase(BaseModel):
    originatorId: Optional[str] = "U65100TN2018PTC124844"
    sanctionReferenceId: Optional[int] = 123
    customerId: Optional[int] = 123
    requestedAmount: Optional[float] = 2000.10
    ifscCode: Optional[str] = "abc"
    branchName: Optional[str] = "Chennai"
    processingFees: Optional[float] = 10.0
    insuranceAmount: Optional[float] = 0.0
    disbursementDate: Optional[str] = "2022-03-10"


class CreateDisbursement(DisbursementBase):
    pass


class DisbursementDB(DisbursementBase):
    id: int


disbursement_metadata = sqlalchemy.MetaData()


disbursement = sqlalchemy.Table(
    "disbursement",
    disbursement_metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("disbursement_reference_id", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("disbursement_status", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("stage", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("utr", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("message", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("status", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("originator_id", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("sanction_reference_id", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("customer_id", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("requested_amount", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("ifsc_code", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("branch_name", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("processing_fees", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("insurance_amount", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("disbursement_date", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("created_date", sqlalchemy.DateTime(), nullable=True),
)