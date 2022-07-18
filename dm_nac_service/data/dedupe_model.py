from datetime import datetime
from typing import Optional, List, Union

import sqlalchemy
from pydantic import BaseModel, Field
from sqlalchemy.dialects.mysql import LONGTEXT


class DedupeTypes(BaseModel):
    type: Optional[str]
    value: Optional[str]


class DedupePan(BaseModel):
    type: Optional[str] = 'PANCARD'
    value: Optional[str] = 'AAAPZ1234C'


class DedupeAadhar(BaseModel):
    type: Optional[str] = 'AADHARCARD'
    value: Optional[str] = '983462897243'


class DedupeTableBase(BaseModel):
    accountNumber: Optional[str] = None
    contactNumber: Optional[str] = None
    customerName: Optional[str] = None
    dateOfBirth: Optional[str] = None
    type: Optional[str] = None
    value: Optional[str] = None
    loanId: Optional[str] = None
    pincode: Optional[str] = None
    created_date: datetime = Field(default_factory=datetime.now)


class CreateDedupe(BaseModel):
    accountNumber: str = '1234313323'
    contactNumber: str = '9999988888'
    customerName: str = 'Gongadi Vijaya Bhaskar'
    dateOfBirth: str = '1996-07-03'
    kycDetailsList: List[Union[DedupeAadhar, DedupePan]] = None
    loanId: str = '12345'
    pincode: str = ' 600209'


class DedupeCreate(BaseModel):
    __root__: List[CreateDedupe]
    #   pass


class DedupeDB(DedupeTableBase):
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
    sqlalchemy.Column("id_type1", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("id_value1", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("id_type2", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("id_value2", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("loan_id", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("pincode", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("dedupe_present", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("response_type", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("result_attribute", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("result_value", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("result_rule_name", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("result_ref_loan_id", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("result_is_eligible", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("result_message", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("ref_originator_id", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("ref_sector_id", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("ref_max_dpd", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("ref_first_name", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("ref_date_of_birth", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("ref_mobile_phone", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("ref_account_number_loan_ref", sqlalchemy.String(length=250), nullable=True),

    # sqlalchemy.Column("request_data", LONGTEXT, nullable=True),

    sqlalchemy.Column("created_date", sqlalchemy.DateTime(), nullable=True),
)

