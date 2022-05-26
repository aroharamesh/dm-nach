from datetime import datetime
from typing import Optional, List

import sqlalchemy
from pydantic import BaseModel, Field
from sqlalchemy.dialects.mysql import LONGTEXT


class DedupeBase(BaseModel):
    type: Optional[str] = 'PANCARD'
    value: Optional[str] = 'AAAPZ1234C'


class DedupeTableBase2(BaseModel):
    accountNumber: Optional[str] = None
    contactNumber: Optional[str] = None
    customerName: Optional[str] = None
    dateofBirth: Optional[str] = None
    loanId: Optional[str] = None
    pincode: Optional[str] = None
    created_date: datetime = Field(default_factory=datetime.now)


class CreateDedupe(BaseModel):
    accountNumber: str = '1234313323'
    contactNumber: str = '9999988888'
    customerName: str = 'Gongadi Vijaya Bhaskar'
    dateofBirth: str = '1996-07-03'
    kycDetailsList: List[DedupeBase]
    loanId: str = ''
    pincode: str = ' 600209'


class DedupeCreate(BaseModel):
    __root__: List[CreateDedupe]
    #   pass


class DedupeDB2(DedupeTableBase2):
    id: int


dedupe_metadata = sqlalchemy.MetaData()


dedupe = sqlalchemy.Table(
    "dedupe",
    dedupe_metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("dedupe_reference_id", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("account_number", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("contact_number", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("customer_name", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("dob", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("id_type", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("id_value", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("loan_id", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("pincode", sqlalchemy.String(length=250), nullable=True),
    # sqlalchemy.Column("request_data", LONGTEXT, nullable=True),

    sqlalchemy.Column("created_date", sqlalchemy.DateTime(), nullable=True),
)

