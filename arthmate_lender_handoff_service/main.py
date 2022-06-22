""" Partner Handoff """

import logging
from logging.config import dictConfig
from functools import lru_cache
import requests
import time
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from requests.auth import HTTPBasicAuth

from .helpers.external_logging_service import log
from . import config
from .helpers import create_underwriting_engine_data, process_underwriting_resp
from .logger.config import LogConfig
from .helpers.functions import (
    create_user_data,
    create_loan_request_data,
    create_user_document_upload_data,
    create_loan_document_upload_data,
    document_upload,
    kyc_document_upload,
    loan_document_upload,
    update_handoff_response,
)
from .helpers.perdix import (
    perdix_enrollment_get,
    perdix_enrollment_update,
    perdix_login,
    perdix_loan_get,
    perdix_loan_update,
)

app = FastAPI()

lender_doc_mapping = {
    "EPIC" : 2,
    "PASSPORT": 3,
    "DRIVINGLICENCE": 8
}

# Adding the logger and log file
dictConfig(LogConfig().dict())
logger = logging.getLogger("arthmate-lender-handoff-service")
logfile_handler = logging.FileHandler("arthmate_lender_handoff_service/logs/server.log")
logger.addHandler(logfile_handler)

headers = {"Content-type": "application/json", "Accept": "application/json"}


@lru_cache()
def get_settings():
    """Function which reads Settings from config file"""
    return config.Settings()


logger = logging.getLogger("arthmate-lender-handoff-service")
logger.setLevel(logging.DEBUG)


@app.post("/process-automator-data", status_code=status.HTTP_200_OK)
async def post_automator_data(
    request_info: Request,
    response: Response,
    settings: config.Settings = Depends(get_settings),
):
    """Function which prepares user data and posts"""
    try:
        payload = await request_info.json()
        payload["partnerHandoffIntegration"]["status"] = "FAILURE"
        customer_data = payload["enrollmentDTO"]["customer"]
        enterprise_data = payload["enterpriseDTO"]
        loan_data = payload["loanDTO"]["loanAccount"]
        repayment_data = payload["repaymentSchedule"] or []
        kyc_data = payload["kycData"]
        timestamp = time.time() * 1000

        user_create_url = settings.user_url
        loan_request_url = settings.loan_url
        user_document_url = settings.user_document_upload_url
        loan_document_url = settings.loan_document_upload_url

        token = perdix_login(settings)["access_token"]
        am_user_uuid = customer_data["oldCustomerId"]

        if am_user_uuid is None:
            user_info = create_user_data(customer_data, enterprise_data)
            user_response = requests.post(
                user_create_url,
                auth=HTTPBasicAuth(settings.username, settings.password),
                json=user_info,
                headers=headers,
            )
            logger.info("Step 1 - Response Status - %s", {user_response})
            log(
                "ARTHMATE",
                "USER_CREATE",
                customer_data["id"],
                timestamp,
                user_info,
                user_response,
                user_response.status_code,
                f"{user_response.content}",
            )

            if (
                user_response.ok
                and "flag" in user_response.json()
                and user_response.json()["flag"]
            ):
                am_user_details = user_response.json()["body"]
                am_user_uuid = am_user_details["uuid"]

        if not am_user_uuid:
            logger.error("User creation or perdix oldCustomerId look up failed")
            update_handoff_response(
                status.HTTP_200_OK,
                response,
                payload,
                f"User lookup failed for {customer_data['id']}",
            )
            return payload

        if customer_data["oldCustomerId"] is None:
            perdix_customer = perdix_enrollment_get(payload, settings, headers, token)
            perdix_customer["oldCustomerId"] = am_user_uuid
            perdix_enrollment_update(perdix_customer, settings, headers, token)

        sm_user_id = customer_data["partnerCustomerId"]
        document_info = create_user_document_upload_data(sm_user_id, am_user_uuid, 5)
        selfie1_image_id = customer_data["selfie1"]
        document_resp = document_upload(
            settings, user_document_url, document_info, selfie1_image_id
        )
        log(
            "ARTHMATE",
            "USER_DOC",
            customer_data["id"],
            timestamp,
            document_info,
            document_resp,
            document_resp.status_code,
            f"{document_resp.content}",
        )

        doc_type = 2
        if customer_data['addressProof'] and customer_data['addressProof'] in lender_doc_mapping:
            doc_type = lender_doc_mapping[customer_data['addressProof']]

        document_info = create_user_document_upload_data(sm_user_id, am_user_uuid, doc_type)
        poa_image_id = customer_data["addressProofImageId"]
        if poa_image_id:
            document_resp = document_upload(
                settings, user_document_url, document_info, poa_image_id
            )
            log(
                "ARTHMATE",
                "USER_DOC",
                customer_data["id"],
                timestamp,
                document_info,
                document_resp,
                document_resp.status_code,
                f"{document_resp.content}",
            )

        document_info = create_user_document_upload_data(sm_user_id, am_user_uuid, 4)
        document_resp = kyc_document_upload(
            settings, user_document_url, document_info, kyc_data
        )
        log(
            "ARTHMATE",
            "USER_DOC",
            customer_data["id"],
            timestamp,
            document_info,
            document_resp,
            document_resp.status_code,
            f"{document_resp.content}",
        )

        loan_info = create_loan_request_data(
            loan_data, customer_data, repayment_data, sm_user_id, am_user_uuid
        )
        loan_response = requests.post(
            loan_request_url,
            auth=HTTPBasicAuth(settings.username, settings.password),
            json=loan_info,
            headers=headers,
        )
        logger.info("Step 3 - Response Status - %s", {loan_response})
        log(
            "ARTHMATE",
            "LOAN_CREATE",
            loan_data["id"],
            timestamp,
            loan_info,
            loan_response,
            loan_response.status_code,
            f"{loan_response.content}",
        )

        if not loan_response.ok or (
            "flag" in loan_response.json() and loan_response.json()["flag"] == False
        ):
            update_handoff_response(
                status.HTTP_200_OK, response, payload, f"{loan_response}"
            )
            return payload

        loan_response_amlid_check = loan_response.json()["body"]
        am_loan_id = loan_response_amlid_check["aml_id"]
        loan = perdix_loan_get(payload, settings, headers, token)
        loan["oldAccountNO"] = am_loan_id
        loan["partnerRemarks"] = am_user_uuid
        loan = perdix_loan_update(loan, settings, headers, token)

        loan_document_upload_info = create_loan_document_upload_data(
            loan_data, customer_data, am_user_uuid, am_loan_id, 6
        )
        doc_url = f"{settings.perdix_form_url}?form_name=sanction_letter_sm&record_id={loan_data['id']}&token={token}"
        document_resp = loan_document_upload(
            settings, loan_document_url, loan_document_upload_info, doc_url, timestamp
        )
        log(
            "ARTHMATE",
            "LOAN_DOC",
            loan_data["id"],
            timestamp,
            loan_document_upload_info,
            document_resp,
            document_resp.status_code,
            f"{document_resp.content}",
        )

        loan_document_upload_info = create_loan_document_upload_data(
            loan_data, customer_data, am_user_uuid, am_loan_id, 7
        )
        doc_url = f"{settings.perdix_form_url}?form_name=loan_agreement_sm&record_id={loan_data['id']}&token={token}"
        document_resp = loan_document_upload(
            settings, loan_document_url, loan_document_upload_info, doc_url, timestamp
        )
        log(
            "ARTHMATE",
            "LOAN_DOC",
            loan_data["id"],
            timestamp,
            loan_document_upload_info,
            document_resp,
            document_resp.status_code,
            f"{document_resp.content}",
        )

        loan = perdix_loan_get(payload, settings, headers, token)
        loan["fiRemarks"] = "Pending for Disbursement"
        loan = perdix_loan_update(loan, settings, headers, token, action="PROCEED")
        logger.info(f"loan {am_loan_id} moved to LMS")
        payload["partnerHandoffIntegration"]["status"] = "SUCCESS"
        payload["partnerHandoffIntegration"]["partnerReferenceKey"] = am_loan_id
        return payload
    except Exception as ex:
        logger.error("Error Occurred: ", ex)
        raise HTTPException(status_code=500, detail=f"lender handoff exception: {ex}")


@app.post("/process-underwriting-data")
async def post_underwriting_data(
    request_info: Request,
    response: Response,
    settings: config.Settings = Depends(get_settings),
):
    """Function for underwriting engine"""
    try:
        timestamp = time.time() * 1000
        payload = await request_info.json()

        # call all the urls from config where the prepared data needs to be posted
        underwriting_engine_login_url = settings.underwriting_engine_login_url
        underwriting_engine_calc_url = settings.underwriting_engine_calc_url
        underwriting_engine_username = settings.underwriting_engine_username
        underwriting_engine_password = settings.underwriting_engine_password

        response.status_code = status.HTTP_400_BAD_REQUEST
        login_payload = {
            "username": underwriting_engine_username,
            "password": underwriting_engine_password,
        }
        login_response = requests.post(
            underwriting_engine_login_url, json=login_payload, headers=headers
        )
        log(
            "SPICEMONEY",
            "UNDERWRITING_LOGIN",
            payload["loanDTO"]["loanAccount"]["id"],
            timestamp,
            login_payload,
            login_response,
            login_response.status_code,
            None,
        )
        if login_response.ok:
            logger.info(
                f"underwriting login succeeded .. moving to underwriting calc for loan - {payload['loanDTO']['loanAccount']['id']}"
            )
            underwriting_payload = create_underwriting_engine_data(payload)
            underwriting_resp = requests.post(
                underwriting_engine_calc_url,
                json=underwriting_payload,
                headers={
                    **headers,
                    "Authorization": "Token " + login_response.json()["token"],
                },
            )
            log(
                "SPICEMONEY",
                "UNDERWRITING_CALC",
                payload["loanDTO"]["loanAccount"]["id"],
                timestamp,
                underwriting_payload,
                underwriting_resp,
                underwriting_resp.status_code,
                None,
            )
            if underwriting_resp.ok:
                response.status_code = 200
                logger.info(
                    f"underwriting calc api succeeded for loan - {payload['loanDTO']['loanAccount']['id']}"
                )
                process_underwriting_resp(
                    payload, underwriting_resp.json(), settings, headers
                )
            else:
                logger.info(
                    f"underwriting calc failed for loan - {payload['loanDTO']['loanAccount']['id']}"
                )
        else:
            logger.info(
                f"underwriting login failed for loan - {payload['loanDTO']['loanAccount']['id']}"
            )
    except Exception as ex:
        logger.exception("Error Occurred: ", ex)
        raise HTTPException(
            status_code=500, detail=f"Underwriting engine api exception: {ex}"
        )

    return payload
