sanction_request_data = {
    "kycDetailsList": [
         {
             "type": "PANCARD ",
             "value": "AAPZ1235C"
         }
    ],
    "dedupeReferenceId": 5138090802722267,
    "gender": "FEMALE",
    "maritalStatus": "MARRIED",
    "pincode": "560010",
    "residenceTypeCode": 1,
    "employmentType": "employeed",
    "city": "bellary",
    "dueDate": "2022-05-25",
    "mobile": "8578636869",
    "fullName": "rana",
    "addressCategoryCode": 1,
    "billingDate": "2022-05-27",
    "assessedIncome": 10000,
    "deliveryAddress": "14th main",
    "DOB": "1990-08-12",
    "sanctionLimit": 300000,
    "partnerCustomerID": "U74999TN1995PTC030252",
    "addressLine1": "lotus residency",
    "addressLine2": "jayanagar 9th block",
    "stateCode": 29,
    "addressLine3": "jayanagar 8th block",
    "PAN": "AAPZ1235C",
    "email": "xyz13@gmail.com",
    "CKYC": "21346"
}


sanction_response_success_data = {
    "content": {
        "message": "Customer ID created successfully",
        "customerId": "572957",
        "clientId": "12345",
        "status": "SUCCESS"
    }
}


sanction_response_error_data = {
    "content": {
        "message": "JSON Validation Failed",
        "status": "ERROR",
        "value": {
            "MISSING_MANDATORY_FIELDS": [
                "sanctionLimit",
                "partnerCustomerID"
            ],
            "FIELDS_WITH_INVALID_CONSTANTS": [
                "gender",
                "maritalStatus"
            ],
        }
    }
}


sanction_status_response_not_found = {
    "content": {
        "status": "ERROR",
        "value": "Customer ID not found"
    }
}

sanction_status_response_in_progress = {
    "content": {
        "status": "SUCCESS",
        "value": {
            "status": "IN_PROGRESS",
            "stage": "SANCTION_CHECK",
            "bureauFetchStatus": "IN_PROGRESS"
        }
    }
}


sanction_status_response_eligible = {
    "content": {
        "status": "SUCCESS",
        "value": {
            "status": "ELIGIBLE",
            "sanctionReferenceId": 354342,
            "bureauFetchStatus": "COMPLETED"
        }
    }
}


sanction_status_response_rejected_bureau = {
    "content": {
        "status": "SUCCESS",
        "value": {
            "status": "REJECTED",
            "stage": "BUREAU_FETCH",
            "bureauFetchStatus": "FAILED"
        }
    }
}


sanction_status_response_rejected_bre = {
    "content": {
        "status": "SUCCESS",
        "value": {
            "status": "REJECTED",
            "stage": "BRE",
            "bureauFetchStatus": "COMPLETED",
            "rejectReason": ["RULE_1", "RULE_2"]
        }
    }
}


sanction_status_response_rejected_server = {
    "content": {
        "status": "SUCCESS",
        "value": {
            "status": "REJECTED",
            "stage": "BRE",
            "rejectReason": "SYSTEM_ERROR"
        }
    }
}


sanction_file_upload_response1 = {
    'status_code': 200,
    "content": {
        "message": "File uploaded Successfully : AADHAR_DOC",
        "status": "SUCCESS"
    }
}

sanction_file_upload_response2 = {
    'status_code': 200,
    "content": {
        "message": "File Replaced Successfully : AADHAR_DOC",
        "status": "SUCCESS"
    }
}