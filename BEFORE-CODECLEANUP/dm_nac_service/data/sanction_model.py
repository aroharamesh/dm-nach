from datetime import datetime
from typing import Optional, List
from enum import Enum

import sqlalchemy
from pydantic import BaseModel, Field
from sqlalchemy.dialects.mysql import LONGTEXT


class SanctionDetail(BaseModel):
    type: Optional[str] = 'PANCARD'
    value: Optional[str] = 'AAAPZ1234C'


class DedupePan(BaseModel):
    type: Optional[str] = 'PANCARD'
    value: Optional[str] = 'AAAPZ1234C'


class DedupeAadhar(BaseModel):
    type: Optional[str] = 'AADHARCARD'
    value: Optional[str] = '983462897243'


class SanctionBase(BaseModel):
    mobile: Optional[str] = '8904311488'
    firstName: Optional[str] = 'Rahul'
    lastName: Optional[str] = ''
    fatherName: Optional[str] = 'KRISHNAMURTHY'
    gender: Optional[str] = 'FEMALE'
    idProofTypeFromPartner: Optional[str] = 'PANCARD'
    idProofNumberFromPartner: Optional[str] = 'AUNPB8013P'
    addressProofTypeFromPartner: Optional[str] = 'AADHARCARD'
    addressProofNumberFromPartner: Optional[str] = '435265431233'
    dob: Optional[str] ='1990-10-06'
    ownedVehicle: Optional[str] = '2W'
    currDoorAndBuilding: Optional[str] = 'jayanagar 9th block'
    currStreetAndLocality: Optional[str] = 'bangalore'
    currLandmark: Optional[str] = 'banashankari circle'
    currCity: Optional[str] = 'bangalore'
    currDistrict: Optional[str] = 'bangalore'
    currState: Optional[str] = 'Karnataka'
    currPincode: Optional[int] = 0
    permDoorAndBuilding: Optional[str] = 'btm layout'
    permLandmark: Optional[str] = ''
    permCity: Optional[str] = 'Bangalore south'
    permDistrict: Optional[str] = 'Bangalore south'
    permState: Optional[str] = 'Karnataka'
    permPincode: Optional[int] = 0
    occupation: Optional[str] = 'SALARIED_OTHER'
    companyName: Optional[str] = 'BlowHorn PRIVATE LIMITED'
    grossMonthlyIncome: Optional[int] = 30000
    netMonthlyIncome: Optional[int] = 45000
    incomeValidationStatus: Optional[str] = 'SUCCESS'
    pan: Optional[str] = 'AUNPB8013P'
    purposeOfLoan: Optional[str] = 'Others-TO BUY GOLD'
    loanAmount: Optional[int] = 10000
    interestRate: Optional[int] = 25
    scheduleStartDate: Optional[str] = '2020-05-17'
    firstInstallmentDate: Optional[str] = '2020-04-11'
    totalProcessingFees: Optional[int] = 900
    gst: Optional[int] = 0
    preEmiAmount: Optional[int] = 0
    emi: Optional[int] = 100
    emiDate: Optional[str] = '2022-04-10'
    emiWeek: Optional[int] = 1
    repaymentFrequency: Optional[str] = 'MONTHLY'
    repaymentMode: Optional[str] = 'NACH'
    tenureValue: Optional[int] = 36
    tenureUnits: Optional[str] = 'MONTHS'
    productName: Optional[str] = 'Personal Loan'
    primaryBankAccount: Optional[str] = 'SPARKM7293241117686902'
    bankName: Optional[str] = 'YES BANK LIMITED'
    modeOfSalary: Optional[str] = 'ONLINE'
    clientId: Optional[str] = '5c1d8168-ef34-41ed-ab23-aab6343qoir'
    dedupeReferenceId: Optional[str] = '5133926057687222'
    email: Optional[str] = 'ramshankarsc92@gmail.com'
    middleName:  Optional[str] = ''
    maritalStatus: Optional[str] = 'MARRIED'
    loanId: Optional[str] = '12351'


class CreateSanction(SanctionBase):
    pass


class SanctionDB(SanctionBase):
    id: int


class FileChoices(str, Enum):
    selfie: Optional[str] = "SELFIE"
    aadharXML: Optional[str] = "AADHAR_XML"
    mitc: Optional[str] = "MITC"
    voter_card: Optional[str] = "VOTER_CARD"
    driving_license: Optional[str] = "DRIVING_LICENSE"
    sanction_letter: Optional[str] = "SANCTION_LETTER"
    pan: Optional[str] = "PAN"
    passport: Optional[str] = "PASSPORT"
    aadhar_doc: Optional[str] = "AADHAR_DOC"
    loan_application: Optional[str] = "LOAN_APPLICATION"
    loan_agreement: Optional[str] = "LOAN_AGREEMENT"


sanction_metadata = sqlalchemy.MetaData()


sanction = sqlalchemy.Table(
    'sanction',
    sanction_metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column('customer_id', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('sanctin_ref_id', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('status', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('stage', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('reject_reason', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('bureau_fetch_status', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('mobile', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('first_name', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('last_name', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('father_name', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('gender', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('id_proof_type_from_partner', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('id_proof_number_from_partner', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('address_proof_type_from_partner', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('address_proof_number_from_partner', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('dob', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('owned_vehicle', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('curr_door_and_building', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('curr_street_and_locality', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('curr_landmark', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('curr_city', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('curr_district', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('curr_state', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('curr_pincode', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('perm_door_and_building', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('perm_landmark', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('perm_city', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('perm_district', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('perm_state', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('perm_pincode', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('occupation', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('company_name', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('gross_monthly_income', sqlalchemy.Integer, nullable=True),
    sqlalchemy.Column('net_monthly_income', sqlalchemy.Integer, nullable=True),
    sqlalchemy.Column('income_validation_status', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('pan', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('purpose_of_loan', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('loan_amount', sqlalchemy.Integer, nullable=True),
    sqlalchemy.Column('interest_rate', sqlalchemy.Integer, nullable=True),
    sqlalchemy.Column('schedule_start_date', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('first_installment_date', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('total_processing_fees', sqlalchemy.Integer, nullable=True),
    sqlalchemy.Column('gst', sqlalchemy.Integer, nullable=True),
    sqlalchemy.Column('pre_emi_amount', sqlalchemy.Integer, nullable=True),
    sqlalchemy.Column('emi', sqlalchemy.Integer, nullable=True),
    sqlalchemy.Column('emi_date', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('emi_week', sqlalchemy.Integer, nullable=True),
    sqlalchemy.Column('repayment_frequency', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('repayment_mode', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('tenure_value', sqlalchemy.Integer, nullable=True),
    sqlalchemy.Column('tenure_units', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('product_name', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('primary_bank_account', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('bank_name', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('mode_of_salary', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('client_id', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('dedupe_reference_id', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('email', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('middle_name', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('marital_status', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('loan_id', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("created_date", sqlalchemy.DateTime(), nullable=True)
)

sanction_fileupload = sqlalchemy.Table(
    'sanction_fileupload',
    sanction_metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column('customer_id', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('file_name', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column('message', sqlalchemy.String(length=2000), nullable=True),
    sqlalchemy.Column('status', sqlalchemy.String(length=250), nullable=True),
    sqlalchemy.Column("created_date", sqlalchemy.DateTime(), nullable=True)
)