from datetime import datetime
from typing import Optional, List

import sqlalchemy
from pydantic import BaseModel, Field
from sqlalchemy.dialects.mysql import LONGTEXT


class SanctionDetail(BaseModel):
    type: Optional[str] = 'PANCARD'
    value: Optional[str] = 'AAAPZ1234C'


class SanctionBase(BaseModel):
    dedupeReferenceId: Optional[str] = None
    gender: Optional[str] = None
    maritalStatus: Optional[str] = None
    pincode: Optional[str] = None
    residenceTypeCode: Optional[str] = None
    employmentType: Optional[str] = None
    city: Optional[str] = None
    dueDate: Optional[str] = None
    mobile: Optional[str] = None
    fullName: Optional[str] = None
    addressCategoryCode: Optional[str] = None
    billingDate: Optional[str] = None
    assessedIncome: Optional[str] = None
    deliveryAddress: Optional[str] = None
    DOB: Optional[str] = None
    sanctionLimit: Optional[str] = None
    partnerCustomerID: Optional[str] = None
    addressLine1: Optional[str] = None
    addressLine2: Optional[str] = None
    stateCode: Optional[str] = None
    addressLine3: Optional[str] = None
    PAN: Optional[str] = None
    email: Optional[str] = None
    CKYC: Optional[str] = None


class CreateSanction(BaseModel):
    kycDetailsList: List[SanctionDetail]
    dedupeReferenceId: Optional[str] = '5138090802722267'
    gender: Optional[str] = 'FEMALE'
    maritalStatus: Optional[str] = 'MARRIED'
    pincode: Optional[str] = '560010'
    residenceTypeCode: Optional[str] = 1
    employmentType: Optional[str] = 'employeed'
    city: Optional[str] = 'bellary'
    dueDate: Optional[str] = '2022-05-25'
    mobile: Optional[str] = '8578636869'
    fullName: Optional[str] = 'rana'
    addressCategoryCode: Optional[str] = 1
    billingDate: Optional[str] = '2022-05-27'
    assessedIncome: Optional[str] = '10000'
    deliveryAddress: Optional[str] = '14th main'
    DOB: Optional[str] = '1990-08-12'
    sanctionLimit: Optional[str] = 300000
    partnerCustomerID: Optional[str] = 'U74999TN1995PTC030252'
    addressLine1: Optional[str] = 'lotus residency'
    addressLine2: Optional[str] = 'jayanagar 9th block'
    stateCode: Optional[str] = 29
    addressLine3: Optional[str] = 'jayanagar 8th block'
    PAN: Optional[str] = 'AAPZ1235C'
    email: Optional[str] = 'xyz12@gmail.com'
    CKYC: Optional[str] = '21346'


class SanctionDB(SanctionBase):
    id: int


sanction_metadata = sqlalchemy.MetaData()


sanction = sqlalchemy.Table(
    "sanction",
    sanction_metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("dedupe_reference_id", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("customer_id", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("client_id", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("status", sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("created_date", sqlalchemy.DateTime(), nullable=True),
)

