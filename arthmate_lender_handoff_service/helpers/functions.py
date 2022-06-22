""" Function which are used in main.py """
import logging
import requests
from requests.auth import HTTPBasicAuth
import urllib.request
import json
import tempfile

logger = logging.getLogger("arthmate-lender-handoff-service")

monthly_income_map = {
    "10k to 20k": "20000",
    "20k to 30k": "30000",
    "30k to 40k": "40000",
    "40k to 50k": "50000",
    "50k& above": "60000",
    "10k": "10000"
}


def create_user_data(data, enterprise_data):
    """Function which prepares user data"""

    sm_user_id = data.get("partnerCustomerId", "SM000001250")
    first_name = data.get("firstName", "")
    middle_name = data.get("middleName", "")
    last_name = data.get("lastName", "")
    first_name = first_name if first_name else ""
    last_name = last_name if last_name else ""
    middle_name = middle_name if middle_name else ""
    full_name = f"{first_name} {middle_name} {last_name}"

    gender = data.get("gender", "")
    gender = "M" if gender == "MALE" else "F"

    father_first_name = data.get("fatherFirstName", "")
    father_middle_name = data.get("fatherMiddleName", "")
    father_last_name = data.get("fatherLastName", "")
    father_first_name = father_first_name if father_first_name else ""
    father_last_name = father_last_name if father_last_name else ""
    father_middle_name = father_middle_name if father_middle_name else ""
    father_full_name = father_first_name + father_middle_name + father_last_name
    date_of_birth = data.get("dateOfBirth", "")
    if "str" != type(date_of_birth).__name__:
        date_of_birth = "{:04d}-{:02d}-{:02d}".format(
            date_of_birth["year"],
            date_of_birth["monthValue"],
            date_of_birth["dayOfMonth"],
        )
    marital_status = data.get("maritalStatus", "")
    marital_status = marital_status.lower()
    if marital_status == "unmarried":
        marital_status = "single"

    mobile_number = str(data.get("mobilePhone", "9862590000"))[-10:]
    email_id = data.get("email", "testsm1@gmail.com")
    door_no = data.get("doorNo", "")
    street = data.get("street", "")
    locality = data.get("locality", "")
    district = data.get("district", "")
    state = data.get("state", "")
    pincode = str(data.get("pincode", ""))
    res_address = "{} {} {}".format(door_no, street, locality)
    shop_name = data.get("shopName", "xyz shop")
    shop_type = data.get("shopType", "Manufacturers")
    shop_address = enterprise_data["doorNo"]
    income = enterprise_data["enterprise"]["monthlyTurnover"] or "10k"
    monthly_income = (
        monthly_income_map[income] if income in monthly_income_map else "10000"
    )
    udhyog_aadhar = "Yes" if data.get("aadhaarNo") else "No"
    uan_number = data.get("aadhaarNo") or None
    poa_type = data.get("poa_type", "1")
    poa_number = data.get("addressProofNo") or "KANKS12345"
    bureau_score = data.get("bureau_score", "650")
    sm_score = data.get("spiceRiskScore", "3")
    sm_loan_eligibility = data.get("loanEligibility", 25000.00)
    pan_no = data.get("panNo", "ALWPG5909L")
    res_type = data.get("res_type", "Rent")
    bank_accounts_info = {}
    if len(data["customerBankAccounts"]) > 0:
        bank_accounts_info = data["customerBankAccounts"][1]

    customer_bank_name = bank_accounts_info.get("customerBankName", "SBI")
    ifsc_code = bank_accounts_info.get("ifscCode", "ICICI00002")
    account_type = bank_accounts_info.get("accountType", "savings")
    account_type = account_type if account_type else "savings"
    account_number = bank_accounts_info.get("accountNumber", "00301530887")
    bank_statements = bank_accounts_info.get("bankStatements", "")
    bank_statement_availability = "Yes" if (len(bank_statements) > 0) else "No"

    user_data = {
        "sm_user_id": sm_user_id,
        "name": full_name,
        "date_of_birth": str(date_of_birth),
        "gender": gender,
        "father_name": father_full_name,
        "marital_status": marital_status,
        "mobile_number": mobile_number,
        "email_id": email_id or "testemail{}@gmail.com".format(sm_user_id),
        "res_address": res_address,
        "res_city": district,
        "res_state": state,
        "res_pin_code": pincode,
        "res_type": res_type,
        "shop_name": shop_name,
        "shop_type": shop_type,
        "shop_address": shop_address,
        "monthly_income": monthly_income,
        "udhyog_aadhar": udhyog_aadhar,
        "uan_number": uan_number,
        "pan_number": pan_no,
        "poa_type": poa_type,
        "poa_number": poa_number,
        "bank_name": customer_bank_name,
        "account_number": account_number,
        "ifsc_code": ifsc_code,
        "account_type": account_type.lower(),
        "bureau_score": bureau_score,
        "sm_score": sm_score,
        "sm_loan_eligibility": sm_loan_eligibility,
        "bank_statement_availability": bank_statement_availability,
    }
    return user_data


def create_loan_request_data(
    loan_data, customer_data, repayment_data, sm_user_id, am_user_token
):
    """Function which prepares loan data"""
    sm_loan_id = loan_data.get("id", "SML00253011")
    loan_amount = loan_data.get("loanAmount", "10000")
    interest_rate = loan_data.get("interestRate", "12")
    disbursement_schedules = [
        {
            "int_amount": schedule["part2"],
            "prin": schedule["part1"],
            "emi_no": schedule["transactionId"],
            "due_date": schedule["valueDateStr"],
            "emi_amount": schedule["amount1"],
        }
        for schedule in repayment_data
    ]
    tenure = loan_data.get("tenure", "")
    processing_fee_in_paisa = (
        loan_data.get("processingFeeInPaisa", "500") / 100
    ) * 1.18
    disbursement_amount = round(loan_amount - processing_fee_in_paisa)
    number_of_edis = len(disbursement_schedules)
    first_name = customer_data.get("firstName", "")
    middle_name = customer_data.get("middleName", "")
    last_name = customer_data.get("lastName", "")
    first_name = first_name if first_name else ""
    last_name = last_name if last_name else ""
    middle_name = middle_name if middle_name else ""
    full_name = f"{first_name} {middle_name} {last_name}"
    eligible_amount = customer_data.get("loanEligibilityAmount", 0)
    vpa_details = get_vpa_detals(customer_data)
    average_6_month_platform_commission = (
        float(customer_data["previousRentDetails"])
        if customer_data["previousRentDetails"]
        else 0
    )
    sm_core = customer_data["spiceRiskScore"]
    bank_statement_availability = "No"  # fix later

    data = {
        "loan_amount": str(loan_amount),
        "interest_rate": str(interest_rate),
        "disbursement_amount": str(disbursement_amount),
        "tenure": str(tenure),
        "repayment_schedule_json": disbursement_schedules,
        "am_user_token": str(am_user_token),
        "sm_user_id": str(sm_user_id),
        "sm_loan_id": str(sm_loan_id),
        "processing_fee": str(processing_fee_in_paisa),
        "number_of_edis": str(number_of_edis),
        "bank_account_holder_name": full_name,
        "bank_statement_availability": bank_statement_availability,
        "bureau_score": "650",
        "sm_score": str(sm_core),
        "sm_loan_eligibility": str(eligible_amount),
        "average_6_month_platform_commission": average_6_month_platform_commission,
        **vpa_details,
    }
    return data


def create_user_document_upload_data(sm_user_id, uuid, document_type):
    """Function which prepares user document upload data"""
    user_document_data = {
        "sm_user_id": sm_user_id,
        "uuid": uuid,
        "document_type": document_type,
    }
    return user_document_data


def create_loan_document_upload_data(
    loan_data, customer_data, uuid, aml_id, document_type
):
    """Function which prepares loan document upload data"""
    sm_loan_id = loan_data["id"]
    time_stamp = customer_data["lastModifiedDate"]
    ip_stamp = customer_data["udf"]["userDefinedFieldValues"]["udf42"] or "127.0.0.1"
    loan_document_data = {
        "uuid": uuid,
        "sm_loan_id": sm_loan_id,
        "aml_id": aml_id,
        "time_stamp": time_stamp,
        "ip_stamp": ip_stamp,
        "document_type": document_type,
    }
    return loan_document_data


def update_handoff_response(status_code, response, payload, api_respose):
    response.status_code = status_code
    payload["partnerHandoffIntegration"]["errorCode"] = status_code
    payload["partnerHandoffIntegration"]["description"] = api_respose


def document_upload(settings, url, document_info, image_id):
    file_url = settings.file_stream_url + image_id
    tmp_file = "/tmp/" + image_id + ".jpg"
    urllib.request.urlretrieve(file_url, tmp_file)

    with open(tmp_file, "rb") as file_handle:
        files = {"file": file_handle}
        document_response = requests.post(
            url,
            auth=HTTPBasicAuth(settings.username, settings.password),
            data=document_info,
            files=files,
        )
        return document_response


def loan_document_upload(settings, url, document_info, doc_url, timestamp):

    tmp_file = "/tmp/" + str(timestamp)[:-2] + ".pdf"
    urllib.request.urlretrieve(doc_url, tmp_file)

    with open(tmp_file, "rb") as file_handle:
        files = {"file": file_handle}
        document_response = requests.post(
            url,
            auth=HTTPBasicAuth(settings.username, settings.password),
            data=document_info,
            files=files,
        )
        return document_response


def kyc_document_upload(settings, url, document_info, kyc_data):
    with tempfile.NamedTemporaryFile(
        delete=True, mode="w+", suffix=".txt"
    ) as file_handle:
        file_handle.write(json.dumps(kyc_data))
        file_handle.flush()
        file_handle.seek(0)
        files = {"file": file_handle}
        document_response = requests.post(
            url,
            auth=HTTPBasicAuth(settings.username, settings.password),
            data=document_info,
            files=files,
        )
        return document_response


def get_vpa_detals(customer_data):
    wallet_details = customer_data["customerBankAccounts"][0]
    wallet = {
        "disbursement_bank_name": wallet_details["customerBankName"],
        "disbursement_bank_account_type": wallet_details["accountType"].lower(),
        "disbursement_bank_account_number": str(wallet_details["accountNumber"]),
        "disbursement_ifsc_code": wallet_details["ifscCode"],
    }

    return wallet
