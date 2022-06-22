from .perdix import perdix_loan_get, perdix_loan_update, perdix_login
from datetime import datetime
import json


def create_underwriting_engine_data(data):
    customer_data = data["enrollmentDTO"]["customer"]
    loan_data = data["loanDTO"]["loanAccount"]
    enterprise_data = data["enterpriseDTO"]
    bureau_response = "{}"
    if len(data["bureauData"]) > 0:
        bureau_data = data["bureauData"][0]
        bureau_response = bureau_data["highMarkInterfaceDetails"]["responseMessage"]

    underwriting_engine_data = {
        "activity": "activity1",
        "alternate_number": customer_data["landLineNo"],
        "application_id": str(loan_data["id"]),
        "bank_statement_flag": False,
        "bank_statement_response": None,
        "bureau_pull_consent_flag": True,
        "bureau_response": json.loads(bureau_response),
        "income": enterprise_data["udf"]["userDefinedFieldValues"]["udf41"],
        "okyc_flag": customer_data["okycVerified"] or False,
        "okyc_timestamp": customer_data["lastModifiedDate"],
        "onboarding_end_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "onboarding_lat": customer_data["latitude"] or "19.172180",
        "onboarding_long": customer_data["longitude"] or "72.955154",
        "onboarding_start_timestamp": customer_data["createdDate"],
        "ref_person_mobile": customer_data["whatsAppMobileNo"],
        "ref_person_name": customer_data["nickName"] or "Temp Name",
        "shop_address": enterprise_data["doorNo"] or "Temp Address",
        "shop_name": customer_data["shopName"],
        "shop_type": enterprise_data["enterprise"]["businessConstitution"],
        "shop_video": "",
        "sma_id": str(customer_data["partnerCustomerId"]),
        "UAN": customer_data["aadhaarNo"],
        "udyog_aadhar_flag": customer_data["cifNo"] != None,
        "borrower_id": str(customer_data["partnerCustomerId"]),
    }
    return underwriting_engine_data


def process_underwriting_resp(payload, underwriting_resp, settings, headers):
    login_resp_json = perdix_login(settings)
    loan_data = perdix_loan_get(
        payload, settings, headers, login_resp_json["access_token"]
    )
    loan_data["partnerLoanAmount"] = underwriting_resp["data"]["loan_amount"]
    loan_data["verificationStatus"] = underwriting_resp["data"]["loan_eligibility"]

    if underwriting_resp["data"]["underwriting_status"] == "APPROVED":
        loan_data["partnerApprovalStatus"] = 1
    elif underwriting_resp["data"]["underwriting_status"] == "REJECTED":
        loan_data["partnerApprovalStatus"] = -1
        if "errors" in underwriting_resp["data"]:
            loan_data["verificationStatus"] = underwriting_resp["data"]["errors"]["error_message"]
    else:
        loan_data["partnerApprovalStatus"] = 0

    perdix_loan_update(loan_data, settings, headers, login_resp_json["access_token"])
