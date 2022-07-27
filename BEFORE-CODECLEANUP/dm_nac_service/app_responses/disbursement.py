disbursement_request_success_response = {
    "content": {
        "message": "Disbursement Request Initiated",
        "status": "SUCCESS",
        "value": {
            "disbursementReferenceId": " 5158578604256970"
        }
    }
}

disbursement_request_error_response1 = {
    "content": {
        "message": "Invalid Sanction Reference Id",
        "status": "ERROR"
    }
}

disbursement_request_error_response2 = {
    "content": {
        "message": "Sanction Check Incomplete",
        "status": "ERROR"
    }
}

disbursement_request_error_response3 = {
    "content": {
        "message": " Requested Amount exceeds Sanction Limit",
        "status": "ERROR"
    }
}

disbursement_status_success_response1 = {
    "content": {
        "status": "SUCCESS",
        "value": {
            "stage": "PENNY_DROP",
            "disbursementStatus": "IN_PROGRESS"
        }
    }
}

disbursement_status_success_response2 = {
    "content": {
        "status": "SUCCESS",
        "value": {
            "utr": "IDFBH22047940173",
            "stage": "AMOUNT_DISBURSEMENT",
            "disbursementStatus": "SUCCESS"
        }
    }
}

disbursement_status_error_response1 = {
    "content": {
        "status": "ERROR",
        "message": "Invalid Disbursement ReferenceId ID"
    }
}

disbursement_status_error_response2 = {
    "content": {
        "status": "ERROR",
        "value": {
            "stage": "PENNY_DROP",
            "status": "FAILED"
        }
    }
}

disbursement_status_error_response3 = {
    "content": {
        "status": "ERROR",
        "value": {
            "stage": "AMOUNT_DISBURSEMENT",
            "status": "FAILED"
        }
    }
}