import json
import urllib.request
from collections import defaultdict
from datetime import datetime

from dm_nac_service.resource.log_config import logger
from fastapi import APIRouter, Depends, status, Request, Response, Body
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from dm_nac_service.routes.dedupe import create_dedupe, find_dedupe
from dm_nac_service.data.database import get_database, sqlalchemy_engine, insert_logs
from dm_nac_service.gateway.nac_perdix_automator import perdix_post_login, perdix_fetch_loan, perdix_update_loan
from dm_nac_service.gateway.nac_sanction import nac_sanction, nac_get_sanction
from dm_nac_service.routes.sanction import create_sanction, find_sanction, sanction_status, find_loan_id_from_sanction
from dm_nac_service.resource.generics import handle_none, hanlde_response_body, hanlde_response_status
from dm_nac_service.data.sanction_model import sanction
from dm_nac_service.commons import get_env_or_fail
from dm_nac_service.app_responses.sanction import sanction_response_rejected_server, sanction_response_eligible, sanction_response_rejected_bureau, sanction_response_rejected_bre
from dm_nac_service.routes.disbursement import find_customer_sanction, create_disbursement
from dm_nac_service.gateway.nac_disbursement import nac_disbursement, disbursement_get_status
from dm_nac_service.data.disbursement_model import (disbursement)
from dm_nac_service.data.sanction_model import (sanction)
router = APIRouter()


NAC_SERVER = 'northernarc-server'


@router.post("/nac-dedupe-automator-data", tags=["Automator"])
async def post_automator_data(
    # Below is for Production setup
    # request_info: Request,
    # response: Response

    # Below is to test manually by providing json data in request body
    request_info: dict = Body(...),

):
    """Function which prepares user data and posts"""
    try:
        # Below is for data published from automator
        # payload = await request_info.json()

        # Below is for data published manually
        payload = request_info

        # Data Preparation to post the data to NAC dedupe endpoint
        customer_data = payload["enrollmentDTO"]["customer"]
        loan_data = payload["loanDTO"]["loanAccount"]
        first_name = customer_data.get("firstName", "")
        middle_name = customer_data.get("", "Dummy")
        last_name = customer_data.get("", "Dummy")
        first_name = first_name if first_name else ""
        last_name = last_name if last_name else ""
        middle_name = middle_name if middle_name else ""
        full_name = f"{first_name} {middle_name} {last_name}"
        date_of_birth = customer_data.get("dateOfBirth", "")
        if "str" != type(date_of_birth).__name__:
            date_of_birth = "{:04d}-{:02d}-{:02d}".format(
                date_of_birth["year"],
                date_of_birth["monthValue"],
                date_of_birth["dayOfMonth"],
            )
        mobile_number = str(customer_data.get("mobilePhone", "9862590000"))[-10:]
        pincode = str(customer_data.get("pincode", ""))
        sm_loan_id = loan_data.get("id", "SML00253011")
        udhyog_aadhar = customer_data.get("aadhaarNo")
        pan_no = customer_data.get("panNo", "ALWPG5909L")
        bank_accounts_info = {}
        if len(customer_data["customerBankAccounts"]) > 0:
            bank_accounts_info = customer_data["customerBankAccounts"][0]
        account_number = bank_accounts_info.get("accountNumber", "00301530887")
        dedupe_data = {
                "accountNumber": account_number,
                "contactNumber": mobile_number,
                "customerName": full_name,
                "dateofBirth": str(date_of_birth),
                "kycDetailsList": [
                    {
                        "type": "PANCARD",
                        "value": pan_no
                    },
                    {
                        "type": "AADHARCARD",
                        "value": udhyog_aadhar
                    }
                ],
                "loanId": str(sm_loan_id),
                "pincode": pincode,
            }

        print('1 - prepared data from automator function', dedupe_data)

        # Posting the data to the dedupe API
        dedupe_response = await create_dedupe(dedupe_data)
        print('12 - coming back to automator function', dedupe_response)
        # dedupe_response_decode = jsonable_encoder(dedupe_response)
        # dedupe_response_status = dedupe_response_decode.get('status_code')
        dedupe_response_status = hanlde_response_status(dedupe_response)
        if(dedupe_response_status == 200):
            print('12a Success - response from create dedupe')
            # response_body = dedupe_response_decode.get('body')
            # response_body_json = json.loads(response_body)
            dedupe_data = hanlde_response_body(dedupe_response)
            print('printing the is dedupe presnet', dedupe_data)
            is_dedupe_present = dedupe_data.get('isDedupePresent', '')
            str_fetch_dedupe_info = dedupe_data.get('dedupeReferenceId', '')

            if (is_dedupe_present == False):

                message_remarks = ''
                update_loan_info = await update_loan('DEDUPE', sm_loan_id, str_fetch_dedupe_info, 'Screening',
                                                         message_remarks,
                                                         'PROCEED', message_remarks)
                print('update_loan_info', update_loan_info)
                if(update_loan_info.status_code == 200):
                    print('14a - updated loan information with dedupe reference to Perdix', update_loan_info)
                    payload['partnerHandoffIntegration']['status'] = 'SUCCESS'
                    payload['partnerHandoffIntegration']['partnerReferenceKey'] = str_fetch_dedupe_info
                else:
                    login_unsuccess = hanlde_response_body(update_loan_info)
                    result = JSONResponse(status_code=500, content=login_unsuccess)
                    payload['partnerHandoffIntegration']['status'] = 'FAILURE'
                    payload['partnerHandoffIntegration']['partnerReferenceKey'] = ''
            else:
                dedupe_response_result = len(dedupe_data.get('results'))
                is_eligible_flag = dedupe_data.get('results')[dedupe_response_result-1].get('isEligible')
                message_remarks = dedupe_data.get('results')[dedupe_response_result-1].get('message')
                if (is_eligible_flag == False):
                    update_loan_info = await update_loan('DEDUPE', sm_loan_id, str_fetch_dedupe_info, 'Rejected',
                                                         message_remarks,
                                                         'PROCEED', message_remarks)

                    if (update_loan_info.status_code == 200):
                        print('14a - updated loan information with dedupe reference to Perdix', update_loan_info)
                        payload['partnerHandoffIntegration']['status'] = 'SUCCESS'
                        payload['partnerHandoffIntegration']['partnerReferenceKey'] = str_fetch_dedupe_info
                    else:
                        update_loan_json = jsonable_encoder(update_loan_info)
                        response_body = update_loan_json.get('body')
                        response_body_json = json.loads(response_body)
                        response_body_error = response_body_json.get('error')
                        response_body_description = response_body_json.get('error_description')
                        login_unsuccess = {"error": response_body_error, "error_description": response_body_description}
                        logger.error(f"{datetime.now()} - post_automator_data - 125 - {login_unsuccess}")
                        result = JSONResponse(status_code=500, content=login_unsuccess)
                        payload['partnerHandoffIntegration']['status'] = 'FAILURE'
                        payload['partnerHandoffIntegration']['partnerReferenceKey'] = ''
                    print('14b - updated loan information with dedupe reference to Perdix', update_loan_info)
                else:
                    update_loan_info = await update_loan('DEDUPE', sm_loan_id, str_fetch_dedupe_info, 'Dedupe',
                                                         message_remarks,
                                                         'PROCEED', message_remarks)
                    if (update_loan_info.status_code == 200):
                        print('14a - updated loan information with dedupe reference to Perdix', update_loan_info)
                        payload['partnerHandoffIntegration']['status'] = 'SUCCESS'
                        payload['partnerHandoffIntegration']['partnerReferenceKey'] = str_fetch_dedupe_info
                    else:
                        update_loan_json = jsonable_encoder((update_loan_info))
                        response_body = update_loan_json.get('body')
                        response_body_json = json.loads(response_body)
                        response_body_error = response_body_json.get('error')
                        response_body_description = response_body_json.get('error_description')
                        login_unsuccess = {"error": response_body_error, "error_description": response_body_description}
                        logger.error(f"{datetime.now()} - post_automator_data - 125 - {login_unsuccess}")
                        result = JSONResponse(status_code=500, content=login_unsuccess)
                        payload['partnerHandoffIntegration']['status'] = 'FAILURE'
                        payload['partnerHandoffIntegration']['partnerReferenceKey'] = ''
                    print('14c - updated loan information with dedupe reference to Perdix', update_loan_info)

            result = payload

        else:
            print('12a Failure - response from create dedupe', dedupe_response_decode)
            dedupe_response_decode_str = str(dedupe_response_decode)
            logger.error(f"{datetime.now()} - post_automator_data - 150 - {dedupe_response_decode_str}")
            result = dedupe_response_decode
            print('error from create dedupe', result)

    except Exception as e:
        logger.exception(f"{datetime.now()} - Issue with post_automator_data function, {e.args[0]}")
        result = JSONResponse(status_code=500, content={"message": f"Issue with post_automator_data function, {e.args[0]}"})
    return result


@router.post("/nac-sanction-automator-data", status_code=status.HTTP_200_OK, tags=["Automator"])
async def post_sanction_automator_data(
    # request_info: Request,
    # response: Response
    # Below is to test manually by providing json data in request body
    request_info: dict = Body(...),
):
    """Function which prepares user data and posts"""
    try:
        # print("coming inside prepare sanction data")
        # payload = await request_info.json()

        # Below is for data published manually
        payload = request_info

        # customer Data
        customer_data = payload["enrollmentDTO"]["customer"]
        first_name = customer_data.get("firstName", "")
        middle_name = customer_data.get("middleName", "Dummy")
        middle_name = handle_none(middle_name, 'Dummy')
        last_name = customer_data.get("lastName", "Dummy")
        last_name = handle_none(last_name, 'Dummy')
        first_name = first_name if first_name else ""
        last_name = last_name if last_name else ""
        middle_name = middle_name if middle_name else ""
        full_name = f"{first_name} {middle_name} {last_name}"
        gender = payload.get("gender", "")
        gender = "MALE" if gender == "MALE" else "FEMALE"
        father_first_name = customer_data.get("fatherFirstName", "")
        father_middle_name = customer_data.get("fatherMiddleName", "")
        father_last_name = customer_data.get("fatherLastName", "")
        father_first_name = father_first_name if father_first_name else ""
        father_last_name = father_last_name if father_last_name else ""
        father_middle_name = father_middle_name if father_middle_name else ""
        father_full_name = father_first_name + father_middle_name + father_last_name
        date_of_birth = customer_data.get("dateOfBirth", "")
        if "str" != type(date_of_birth).__name__:
            date_of_birth = "{:04d}-{:02d}-{:02d}".format(
                date_of_birth["year"],
                date_of_birth["monthValue"],
                date_of_birth["dayOfMonth"],
            )
        mobile_number = str(customer_data.get("mobilePhone", "9862590000"))[-10:]
        pincode = str(customer_data.get("pincode", ""))
        udhyog_aadhar = customer_data.get("aadhaarNo")
        pan_no = customer_data.get("panNo", "ALWPG5909L")
        owned_vehicle = customer_data.get("", "2W")
        curr_door_number = customer_data.get("doorNo", "jayanagar201")
        curr_locality = customer_data.get("mailingLocality", "bangalore")
        curr_city = customer_data.get("mailingLocality", "bangalore")
        perm_city = customer_data.get("locality", "bangalore")
        curr_district = customer_data.get("district", "bangalore")
        # curr_city=customer_data.get("","bangalore")
        curr_state = customer_data.get("state", "Karnataka")
        email_id = customer_data.get("email", "testsm1@gmail.com")
        maritual_status = customer_data.get("maritalStatus", "MARRIED")
        last_name = last_name if last_name else ""
        permanent_landmark = customer_data.get("landmark", "VTU")
        permanent_landmark = handle_none(permanent_landmark, 'VTU')
        current_landmark = customer_data.get("landmark", "VTU")
        current_landmark = handle_none(current_landmark, 'BLR')
        if (current_landmark is None):
            current_landmark = 'VTU'

        bank_accounts_info = {}
        if len(customer_data["customerBankAccounts"]) > 0:
            bank_accounts_info = customer_data["customerBankAccounts"][0]
        account_number = bank_accounts_info.get("accountNumber", "1234313323")
        customer_bank_name = bank_accounts_info.get("customerBankName", "YES BANK LIMITED")

        occupation_info = {}
        if len(customer_data["familyMembers"]) > 0:
            occupation_info = customer_data["familyMembers"][0]
        curr_occupation = occupation_info.get("occupation", "SALARIED_OTHER")
        mode_salary = occupation_info.get("", "ONLINE")
        installment_info = {}

        income_info = {}
        if len(customer_data["familyMembers"]) > 0:
            income_info = customer_data["familyMembers"][0]["incomes"][0]
        gross_income = income_info.get("incomeEarned", 30000)
        net_income = income_info.get("incomeEarned", 40000)

        emi_info = {}
        if len(customer_data["liabilities"]) > 0:
            emi_info = customer_data["liabilities"][0]
        emi_date = emi_info.get("", "2022-04-10")

        repayment_info = {}
        if len(customer_data["verifications"]) > 0:
            repayment_info = customer_data["verifications"][0]

        repayment_mode = repayment_info.get("", "NACH")

        # Loan Data
        loan_data = payload["loanDTO"]["loanAccount"]
        sm_loan_id = loan_data.get("id", "SML00253011")
        loan_purpose = loan_data.get("requestedLoanPurpose", "Others-TO BUY GOLD")
        loan_amount = loan_data.get("loanAmount", "10000")
        interest_rate = loan_data.get("interestRate", "25")
        schedule_date = loan_data.get("scheduleStartDate", "")
        if len(loan_data["disbursementSchedules"]) > 0:
            installment_info = loan_data["disbursementSchedules"][0]
        installment_date = installment_info.get("", "2020-04-11")


        if "str" != type(schedule_date).__name__:
            schedule_date = "{:04d}-{:02d}-{:02d}".format(
                schedule_date["year"],
                schedule_date["monthValue"],
                schedule_date["dayOfMonth"],
            )

        process_fee = loan_data.get("processingFeeInPaisa", 900)
        pre_emi = loan_data.get("", 0)
        max_emi = loan_data.get("emi", 100)
        gst = loan_data.get("", 0)

        frequency = loan_data.get("frequency", "M")
        if(frequency == 'M'):
            # repayment_frequency = 'MONTHLY'
            repayment_frequency = 'WEEKLY'
            tenure_unit = 'MONTHS'
        if(frequency == 'W'):
            repayment_frequency = 'WEEKLY'
            tenure_unit = 'WEEKS'
        if (frequency == 'D'):
            repayment_frequency = 'DAILY'
            tenure_unit = 'DAYS'
        if (frequency == 'Y'):
            tenure_unit = 'YEARS'
        if (frequency == 'F'):
            repayment_frequency = 'FORTNIGHTLY'

        tenure_value = loan_data.get("tenure", 36)
        tenure_value_int = int(tenure_value)
        product_name = loan_data.get("productCode", "Personal Loan")
        client_id = loan_data.get("customerId", "12345")

        sanction_data = {
                "mobile": mobile_number,
                "firstName": first_name,
                "lastName": last_name,
                "fatherName": father_full_name,
                "gender": gender,
                "idProofTypeFromPartner": "PANCARD",
                "idProofNumberFromPartner": pan_no,
                "addressProofTypeFromPartner": "AADHARCARD",
                "addressProofNumberFromPartner": udhyog_aadhar,
                "dob": str(date_of_birth),
                "ownedVehicle": owned_vehicle,
                "currDoorAndBuilding": curr_door_number,
                "currStreetAndLocality":curr_locality,
                "currLandmark": current_landmark,
                "currCity": curr_city,
                "currDistrict": curr_district,
                "currState": curr_state,
                "currPincode": pincode,
                "permDoorAndBuilding": curr_door_number,
                "permLandmark": permanent_landmark,
                "permCity":perm_city,
                "permDistrict": curr_district,
                "permState": curr_state,
                "permPincode": pincode,
                "occupation": curr_occupation,
                "companyName": "",
                "clientId": str(client_id),
                "grossMonthlyIncome": gross_income,
                "netMonthlyIncome": net_income,
                "incomeValidationStatus": "",
                "pan": pan_no,
                "purposeOfLoan":loan_purpose ,
                "loanAmount":loan_amount ,
                "interestRate":interest_rate ,
                "scheduleStartDate": schedule_date,
                "firstInstallmentDate": installment_date,
                "totalProcessingFees": process_fee,
                "gst": gst,
                "preEmiAmount": pre_emi,
                "emi": max_emi,
                "emiDate": emi_date,
                "emiWeek": "",
                "repaymentFrequency": repayment_frequency,
                "repaymentMode": repayment_mode,
                "tenureValue": tenure_value_int,
                "tenureUnits": tenure_unit,
                "productName": product_name,
                "primaryBankAccount": account_number,
                "bankName": customer_bank_name,
                "modeOfSalary": mode_salary,
                # "dedupeReferenceId": dedupe_reference_id,
                "email": email_id,
                "middleName": middle_name,
                "maritalStatus": maritual_status,
                "loanId": str(sm_loan_id),
                }

        print('1 - Sanction Data from Perdix and Sending the data to create sanction function', sanction_data)
        sanction_response = await create_sanction(sanction_data)
        sanction_response_decode = jsonable_encoder(sanction_response)
        sanction_response_status = sanction_response_decode.get('status_code')

        if(sanction_response_status == 200):
            print('CLEAR FROM CREATE SANCTION')
            print('100 - response back from NAC ', sanction_response)

            get_sanction_ref = await find_sanction(sm_loan_id)
            get_sanction_ref_decode = jsonable_encoder(get_sanction_ref)
            get_sanction_ref_status = get_sanction_ref_decode.get('status_code')
            if(get_sanction_ref_status == 200):
                print('101 - FOUND CUSTOMER ID FROM DB', get_sanction_ref)
                response_body = get_sanction_ref_decode.get('body')
                response_body_json = json.loads(response_body)
                print('printing referece id ', response_body_json)
                # customer_response_id = str(response_body_json.get('content').get('value'))
                reference_id = str(response_body_json.get('customerId'))
                message_remarks = 'Customer Created Successfully'

                # To Update Perdix with Sanction Reference ID
                update_loan_info = await update_loan('SANCTION', sm_loan_id, reference_id, 'Dedupe', message_remarks,
                                                     'PROCEED', message_remarks)
                update_loan_info_decode = jsonable_encoder(update_loan_info)
                update_loan_info_status = update_loan_info_decode.get('status_code')
                if(update_loan_info_status == 200):
                    print('customer id updated success in perdix')
                    payload['partnerHandoffIntegration']['status'] = 'SUCCESS'
                    payload['partnerHandoffIntegration']['partnerReferenceKey'] = reference_id
                    result = payload
                else:
                    print('customer id not updated success in perdix')
                    response_body = update_loan_info_decode.get('body')
                    response_body_json = json.loads(response_body)
                    response_body_error = response_body_json.get('error')
                    response_body_description = response_body_json.get('error_description')
                    update_unsuccess = {"error": response_body_error, "error_description": response_body_description}
                    logger.error(f"{datetime.now()} - post_sanction_automator_data - 426 - {update_unsuccess}")
                    result = JSONResponse(status_code=500, content=update_unsuccess)
                    payload['partnerHandoffIntegration']['status'] = 'FAILURE'
                    payload['partnerHandoffIntegration']['partnerReferenceKey'] = ''
                    result = payload
            else:
                print('101 - NOT FOUND CUSTOMER ID FROM DB', get_sanction_ref)
                print('customer id not updated success in perdix')
                response_body = sanction_response_decode.get('body')
                response_body_json = json.loads(response_body)
                response_body_error = response_body_json.get('error')
                response_body_description = response_body_json.get('error_description')
                update_unsuccess = {"error": response_body_error, "error_description": response_body_description}
                logger.error(f"{datetime.now()} - post_sanction_automator_data - 426 - {update_unsuccess}")
                result = JSONResponse(status_code=500, content=update_unsuccess)
                payload['partnerHandoffIntegration']['status'] = 'FAILURE'
                payload['partnerHandoffIntegration']['partnerReferenceKey'] = ''
                result = payload
        else:
            response_body = sanction_response_decode.get('body')
            response_body_json = json.loads(response_body)
            response_body_error = response_body_json.get('error')
            response_body_error_description = response_body_json.get('error_description')
            app_log_error = {"error": response_body_error, "error_description": response_body_error_description}
            logger.error(f"{datetime.now()} - post_sanction_automator_data - 452 - {app_log_error}")
            result = JSONResponse(status_code=500, content=app_log_error)
            payload['partnerHandoffIntegration']['status'] = 'FAILURE'
            payload['partnerHandoffIntegration']['partnerReferenceKey'] = ''
            result = payload
    except Exception as e:
        logger.exception(f"{datetime.now()} - Issue with post_sanction_automator_data function, {e.args[0]}")
        result = JSONResponse(status_code=500,
                              content={"message": f"Issue with post_automator_data function, {e.args[0]}"})
    return result


@router.post("/nac-disbursement-automator-data", status_code=status.HTTP_200_OK, tags=["Automator"])
async def post_disbursement_automator_data(
    # request_info: Request,
    # response: Response
    # Below is to test manually by providing json data in request body
    request_info: dict = Body(...),
):
    try:
        database = get_database()
        # print("coming inside prepare sanction data")
        # payload = await request_info.json()

        # Below is for data published manually
        payload = request_info
        print('nac-disbursement-automator-data')
        customer_data = payload["enrollmentDTO"]["customer"]
        loan_data = payload["loanDTO"]["loanAccount"]
        sm_loan_id = loan_data.get("id", "SML00253011")
        requested_amount = loan_data.get("loanAmountRequested", 2000.0)
        bank_accounts_info = {}
        if len(customer_data["customerBankAccounts"]) > 0:
            bank_accounts_info = customer_data["customerBankAccounts"][0]
        ifsc_code = bank_accounts_info.get("ifscCode", "abc")
        branch_name = bank_accounts_info.get("customerBankBranchName", "Chennai")
        insurance_fee = loan_data.get("", 0.0)
        processing_fee = loan_data.get("processingFeeInPaisa", 10.0)
        disbursement_date = loan_data.get("", "2022-03-10")
        print('1 - Fetch customer Id and Sanction Reference Id from DB', sm_loan_id)
        customer_sanction_response = await find_customer_sanction(sm_loan_id)
        sanction_ref_id = customer_sanction_response['sanctionRefId']
        customer_id = customer_sanction_response['customerId']
        print('2 - Response from DB with customer id and sanction ref id', customer_sanction_response)
        originator_id = get_env_or_fail(NAC_SERVER, 'originator-id', NAC_SERVER + 'originator ID not configured')
        print('3 - Originator ID from env', originator_id)

        disbursement_info = {
            "originatorId": originator_id,
            "sanctionReferenceId": int(sanction_ref_id),
            "customerId": int(customer_id),
            "requestedAmount": requested_amount,
            "ifscCode": ifsc_code,
            "branchName": branch_name,
            "processingFees": processing_fee,
            "insuranceAmount": insurance_fee,
            "disbursementDate": disbursement_date
        }
        store_record_time = datetime.now()
        disbursement_db_info = {
            'customer_id': customer_id,
            'originator_id': originator_id,
            'sanction_reference_id': sanction_ref_id,
            'requested_amount': requested_amount,
            'ifsc_code': ifsc_code,
            'branch_name': branch_name,
            'processing_fees': processing_fee,
            'insurance_amount': insurance_fee,
            'disbursement_date': disbursement_date,
            'created_date': store_record_time,
        }
        print('4 - Data Prepared to post to NAC disbursement endpoint', disbursement_info)
        # Real Endpoint
        nac_disbursement_response = await create_disbursement(disbursement_info)
        print('5 - Response from NAC disbursement endpoint', nac_disbursement_response)
        disbursement_status = nac_disbursement_response['content']['status']
        if(disbursement_status == 'SUCCESS'):
            disbursement_message = nac_disbursement_response['content']['message']
            disbursement_reference_id = nac_disbursement_response['content']['value']['disbursementReferenceId']
            payload['partnerHandoffIntegration']['status'] = 'SUCCESS'
            payload['partnerHandoffIntegration']['partnerReferenceKey'] = disbursement_reference_id
            update_loan_info = await update_loan('DISBURSEMENT', sm_loan_id, disbursement_reference_id, 'Dedupe', disbursement_message,
                                                 'PROCEED', disbursement_message)


        # disbursement_response_message = nac_disbursement_response['content']['message']
        # disbursement_response_status = nac_disbursement_response['content']['status']
        # if (disbursement_response_status == 'SUCCESS'):
        #     disbursement_info['message'] = disbursement_response_message
        #     disbursement_info['status'] = disbursement_response_status
        #     disbursement_info['disbursement_reference_id'] = nac_disbursement_response['content']['value'][
        #         'disbursementReferenceId']
        #     disbursement_ref_id = nac_disbursement_response['content']['value'][
        #         'disbursementReferenceId']
        #     disbursement_db_info['message'] = disbursement_response_message
        #     disbursement_db_info['status'] = disbursement_response_status
        #     disbursement_db_info['disbursement_reference_id'] = nac_disbursement_response['content']['value'][
        #         'disbursementReferenceId']
        #     payload['partnerHandoffIntegration']['status'] = 'SUCCESS'
        #     payload['partnerHandoffIntegration']['partnerReferenceKey'] = disbursement_ref_id
        #
        #     insert_query = disbursement.insert().values(disbursement_db_info)
        #     # print('query', insert_query)
        #     disbursement_id = await database.execute(insert_query)
        # else:
        #     disbursement_info['message'] = disbursement_response_message
        #     disbursement_info['status'] = disbursement_response_status

        # get_sanction_from_db = await get_sanction_or_404(sanction_reference_id)
        # print('get_disbursement_from_db', get_disbursement_from_db)

        # if (get_sanction_from_db is None):
        #     insert_query = disbursement.insert().values(disbursement_info)
        #     # print('query', insert_query)
        #     disbursement_id = await database.execute(insert_query)
        # else:
        #     result = JSONResponse(status_code=500, content={"message": f"{sanction_reference_id} is already present"})




        # result = {"function": "nac-disbursement-automator-data"}
        return payload
    except Exception as e:
        print(e)


@router.get("/perdix/{loan_id}", status_code=status.HTTP_200_OK, tags=["Perdix"])
async def get_loan(loan_id):
    result = await perdix_post_login()
    # print(result)
    get_perdix_loan_data = await perdix_fetch_loan(loan_id)
    # print('getting customer', get_perdix_data)

    return get_perdix_loan_data


@router.post("/perdix/update-loan", tags=["Perdix"])
async def update_loan(

    # request_info: Request,
    # response: Response

    # For testing manually
    # loan_info: dict = Body(...),
    url_type: str,
    loan_id: int,
    reference_id: str,
    stage: str,
    reject_reason: str,
    loan_process_action: str,
    remarks: str
):
    try:
        # result = loan_info

        #  For testing manually
        # loan_update_response = await perdix_update_loan(loan_info)
        # result = loan_update_response

        # For Real updating the loan information
        print('coming here inside of update_loan')
        get_loan_info = await perdix_fetch_loan(loan_id)

        print('coming after inside of update_loan', type(get_loan_info) )
        loan_info_response_decode = jsonable_encoder(get_loan_info)
        loan_response_decode_status = loan_info_response_decode.get('status_code')
        if(loan_response_decode_status == 200):
            print('got the loan info')
            response_body = loan_info_response_decode.get('body')
            get_loan_info = json.loads(response_body)
            print('got the loan info sdafasdf', get_loan_info)
            json_data_version = get_loan_info.get('version')
            if "rejectReason" in get_loan_info:
                get_loan_info['rejectReason'] = reject_reason
            get_loan_info['stage'] = stage
            if "remarks1" in get_loan_info:
                get_loan_info['remarks1'] = "Testing remarks1"
            if "loanProcessAction" in get_loan_info:
                get_loan_info['loanProcessAction'] = "Testing loanProcessAction"
            if "accountUserDefinedFields" in get_loan_info:
                if (url_type == 'DEDUPE'):
                    print('inside update loan ', reference_id)
                    get_loan_info['accountUserDefinedFields']['userDefinedFieldValues']['udf41'] = reference_id

                if (url_type == 'SANCTION'):
                    get_loan_info['accountUserDefinedFields']['userDefinedFieldValues']['udf42'] = reference_id

                if (url_type == 'SANCTION-REFERENCE'):
                    get_loan_info['accountUserDefinedFields']['userDefinedFieldValues']['udf43'] = reference_id

                if (url_type == 'DISBURSEMENT'):
                    get_loan_info['accountUserDefinedFields']['userDefinedFieldValues']['udf44'] = reference_id

                if (url_type == 'DISBURSEMENT-ITR'):
                    get_loan_info['accountUserDefinedFields']['userDefinedFieldValues']['udf45'] = reference_id
            if(stage == 'Rejected'):
                prepare_loan_info = {
                    "loanAccount": get_loan_info,
                    "loanProcessAction": loan_process_action,
                    "stage": stage,
                    "remarks": remarks,
                    "rejectReason": reject_reason
                }
            else:
                prepare_loan_info = {
                    "loanAccount": get_loan_info,
                    "loanProcessAction": loan_process_action,
                    "remarks": remarks,
                    "rejectReason": ''
                }
            print('before updateing perdix loan', prepare_loan_info)
            update_perdix_loan = await perdix_update_loan(prepare_loan_info)
            update_perdix_decode = jsonable_encoder(update_perdix_loan)
            perdix_update_loan_response_decode_status = update_perdix_decode.get('status_code')
            if(perdix_update_loan_response_decode_status == 200):
                # result = update_perdix_loan
                response_body = update_perdix_decode.get('body')
                response_body_json = json.loads(response_body)
                print('after updateing perdix loan', response_body_json)

                result = JSONResponse(status_code=200, content=response_body_json)
            else:
                response_body = update_perdix_decode.get('body')
                response_body_json = json.loads(response_body)
                response_body_error = response_body_json.get('error')
                response_body_error_description = response_body_json.get('error_description')
                log_error = {"error": response_body_error, "error_description": response_body_error_description}
                # log_id = await insert_logs('PERDIX', 'PERDIX', 'UPDATING-LOAN', response_body_json.error, response_body_json.error_description,
                #                            datetime.now())
                logger.error(f"{datetime.now()} - update_loan - 573 - {log_error}")
                result = JSONResponse(status_code=404, content=log_error)

        else:
            print('did not get the loan info', loan_info_response_decode)
            response_body = loan_info_response_decode.get('body')
            response_body_json = json.loads(response_body)
            response_body_error = response_body_json.get('error')
            response_body_error_description = response_body_json.get('error_description')
            log_error = {"error": response_body_error, "error_description": response_body_error_description}
            logger.error(f"{datetime.now()} - update_loan - 573 - {log_error}")
            result = JSONResponse(status_code=404, content=log_error)
    except Exception as e:
        logger.exception(f"Issue with update_loan function, {e.args[0]}")
        result = JSONResponse(status_code=500, content={"message": f"Error Occurred at DB level - {e.args[0]}"})
    return result



@router.post("/sanction/upload-document", tags=["Perdix"])
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


@router.post("/sanction/update-sanction-in-db", tags=["Perdix"])
async def update_sanction_in_db():
    try:
        # settings_dict = await get_settings()
        # for items in settings_dict:
        #     iterations_count = items[2]
        #     records_count = items[1]
        customer_array = []
        database = get_database()
        print('coming inside get_pending_sanctions ')
        # query = sanction.select().where(and_(perdix_customer.c.pending.is_(True), perdix_customer.c.iterations<=iterations_count))
        query = sanction.select()
        service_sanction_array = await database.fetch_all(query)
        print('get_pending_sanctions ', service_sanction_array)
        array_length = len(service_sanction_array)
        sanction_array = service_sanction_array
        # # for index in range(len(sanction_array)):
        # #     for key in sanction_array[index]:
        # #         print(sanction_array[index][key])
        #
        # # for dict_item in sanction_array:
        # #     for key in dict_item:
        # #         print(dict_item[key])
        # collect = defaultdict(dict)
        # for key in sanction_array:
        #     collect[key['Name']] = key['customer_id']
        #
        # print(dict(collect))

        for i in sanction_array:
            print(i[1])
            customer_id = i[1]
            sm_loan_id = i[61]
            print('loan ID is ', sm_loan_id)
            # response_sanction_status = await nac_get_sanction('status', i[1])

            # Rejected Scenario
            # response_sanction_status = sanction_response_rejected_server

            # Sanction Reference ID Scenario
            response_sanction_status = sanction_response_eligible

            # Sanction Reference ID Reject Reason
            # response_sanction_status = sanction_response_rejected_bre

            # Sanction Reference ID Scenario
            # response_sanction_status = sanction_response_rejected_bureau

            sanction_status = response_sanction_status['content']['status']

            if(sanction_status == 'SUCCESS'):
                print('inside SUCCESS')
                sanction_status_value = response_sanction_status['content']['value']
                sanction_status_value_status = response_sanction_status['content']['value']['status']
                if(sanction_status_value_status == 'ELIGIBLE'):
                    print('inside ELIGIBLE')
                    sanction_status_value_reference_id = response_sanction_status['content']['value']['sanctionReferenceId']
                    sanction_status_value_bureau_fetch = response_sanction_status['content']['value']['bureauFetchStatus']
                    print('coming here', sanction_status_value_reference_id , sanction_status_value_bureau_fetch)
                    query = sanction.update().where(sanction.c.customer_id == customer_id).values(
                        status=sanction_status_value_status,
                        # stage=sanction_status_value_stage,
                        sanctin_ref_id=sanction_status_value_reference_id,
                        bureau_fetch_status=sanction_status_value_bureau_fetch)
                    sanction_updated = await database.execute(query)
                    update_loan_info = await update_loan('SANCTION-REFERENCE', sm_loan_id, sanction_status_value_reference_id, 'Dedupe',
                                                         sanction_status_value_bureau_fetch,
                                                         'PROCEED', sanction_status_value_bureau_fetch)
                elif(sanction_status_value_status == 'REJECTED'):
                    print('inside REJECTED')
                    sanction_status_value_stage = response_sanction_status['content']['value'][
                        'stage']
                    sanction_status_value_bureau_fetch = response_sanction_status['content']['value'][
                        'bureauFetchStatus']
                    if(sanction_status_value_stage == 'BUREAU_FETCH'):
                        print('inside BUREAU_FETCH')

                        query = sanction.update().where(sanction.c.customer_id == customer_id).values(
                            status=sanction_status_value_status,
                            stage=sanction_status_value_stage,
                            bureau_fetch_status=sanction_status_value_bureau_fetch)
                        sanction_updated = await database.execute(query)
                        update_loan_info = await update_loan('SANCTION', sm_loan_id, '',
                                                             'Rejected',
                                                             sanction_status_value_bureau_fetch,
                                                             'PROCEED', sanction_status_value_bureau_fetch)
                    else:
                        print('inside else BUREAU_FETCH')
                        sanction_status_value_reject_reason = str(response_sanction_status['content']['value'][
                            'rejectReason'])
                        print(sanction_status_value_reject_reason)
                        query = sanction.update().where(sanction.c.customer_id == customer_id).values(
                            status=sanction_status_value_status,
                            stage=sanction_status_value_stage,
                            reject_reason=sanction_status_value_reject_reason,
                            bureau_fetch_status=sanction_status_value_bureau_fetch)
                        sanction_updated = await database.execute(query)
                        update_loan_info = await update_loan('SANCTION', sm_loan_id, '',
                                                             'Rejected',
                                                             sanction_status_value_reject_reason,
                                                             'PROCEED', sanction_status_value_reject_reason)
                else:
                    print('inside else not eligible')
                    sanction_status_value_stage = response_sanction_status['content']['value'][
                        'stage']
                    sanction_status_value_bureau_fetch = response_sanction_status['content']['value'][
                        'bureauFetchStatus']
                    query = sanction.update().where(sanction.c.customer_id == customer_id).values(status=sanction_status_value_status,
                                                                                          stage=sanction_status_value_stage,
                                                                                          # reject_reason=rejectReason,
                                                                                          bureau_fetch_status=sanction_status_value_bureau_fetch)
                    sanction_updated = await database.execute(query)
                    update_loan_info = await update_loan('SANCTION', sm_loan_id, '',
                                                         'Dedupe',
                                                         sanction_status_value_bureau_fetch,
                                                         'PROCEED', sanction_status_value_bureau_fetch)


            # return customer_updated

            # print(response_sanction_status)
            # print(sanction_status_value)


        # print(sanction_array)

        # if records_count >= array_length:
        #     customer_array = perdix_customer_array
        # else:
        #     customer_array = perdix_customer_array[:records_count]
        # return customer_array
        return sanction_array
    except Exception as e:
        log_id = await insert_logs('MYSQL', 'DB', 'GET-PENDING-CUSTOMERS', '500', {e.args[0]},
                                   datetime.now())
        result = JSONResponse(status_code=500, content={"message": f"Error Occurred at DB level - {e.args[0]}"})



@router.post("/disbursement/update-disbursement-in-db", tags=["Perdix"])
async def update_disbursement_in_db():
    try:
        database = get_database()
        print('coming inside update_disbursement_in_db ')
        # query = sanction.select().where(and_(perdix_customer.c.pending.is_(True), perdix_customer.c.iterations<=iterations_count))
        query = disbursement.select()
        service_disbursement_array = await database.fetch_all(query)
        print('get_pending_sanctions ', service_disbursement_array)
        array_length = len(service_disbursement_array)
        disbursement_array = service_disbursement_array
        result = {"function": "update_disbursement_in_db"}
        for i in disbursement_array:
            # print(i[1])
            disbursement_ref_id = i[1]
            sanction_ref_id = i[8]
            # query = sanction.select().where(sanction.c.sanctin_ref_id == sanction_ref_id)
            # disbursement_sanction_id = await database.fetch_one(query)
            disbursement_sanction_id = await find_loan_id_from_sanction(sanction_ref_id)
            disb_sanc_data = disbursement_sanction_id
            print('loan id from disbursement', disb_sanc_data.get('loanID'), sanction_ref_id)
            sm_loan_id = disb_sanc_data.get('loanID')
            # print('disbursement_ref_id ID is ', disbursement_ref_id)
            get_disbursement_response = await disbursement_get_status('disbursement', disbursement_ref_id)
            print('disbursement response ', get_disbursement_response)
            get_disbursement_response_content = get_disbursement_response['content']
            get_disbursement_response_status = get_disbursement_response['content']['status']
            print('disbursement response status - ', get_disbursement_response_status)
            if(get_disbursement_response_status == 'SUCCESS'):
                get_disbursement_response_stage = get_disbursement_response['content']['value']['stage']
                print('disbursement response stage -', get_disbursement_response_stage)
                if(get_disbursement_response_stage == 'AMOUNT_DISBURSEMENT'):
                    get_disbursement_response_utr = get_disbursement_response['content']['value']['utr']
                    get_disbursement_response_disbursement_status = get_disbursement_response['content']['value']['disbursementStatus']
                    query = disbursement.update().where(disbursement.c.disbursement_reference_id == disbursement_ref_id).values(
                        status=get_disbursement_response_status,
                        stage=get_disbursement_response_stage,
                        disbursement_status=get_disbursement_response_disbursement_status,
                        message='',
                        utr=get_disbursement_response_utr)
                    disbursement_updated = await database.execute(query)
                    update_loan_info = await update_loan('DISBURSEMENT-ITR', sm_loan_id,
                                                         get_disbursement_response_utr, 'Dedupe',
                                                         get_disbursement_response_disbursement_status,
                                                         'PROCEED', get_disbursement_response_disbursement_status)
                    print('disbursement response AMOUNT_DISBURSEMENT -', get_disbursement_response_utr, get_disbursement_response_disbursement_status)
                else:
                    get_disbursement_response_disbursement_status = get_disbursement_response['content']['value']['disbursementStatus']
                    query = disbursement.update().where(
                        disbursement.c.disbursement_reference_id == disbursement_ref_id).values(
                        status=get_disbursement_response_status,
                        stage=get_disbursement_response_stage,
                        disbursement_status=get_disbursement_response_disbursement_status,
                        message='',
                        utr='')
                    disbursement_updated = await database.execute(query)
                    print('disbursement response AMOUNT_DISBURSEMENT -', get_disbursement_response_disbursement_status)
            else:
                if("value" in get_disbursement_response_content):

                    get_disbursement_response_stage = get_disbursement_response['content']['value']['stage']
                    get_disbursement_response_value_status = get_disbursement_response['content']['value']['status']
                    query = disbursement.update().where(
                        disbursement.c.disbursement_reference_id == disbursement_ref_id).values(
                        status=get_disbursement_response_status,
                        stage=get_disbursement_response_stage,
                        disbursement_status=get_disbursement_response_value_status,
                        message='',
                        utr='')
                    disbursement_updated = await database.execute(query)
                    print('yes value is there', get_disbursement_response_stage, get_disbursement_response_value_status )
                else:
                    get_disbursement_response_message = get_disbursement_response['content']['message']
                    query = disbursement.update().where(
                        disbursement.c.disbursement_reference_id == disbursement_ref_id).values(
                        status=get_disbursement_response_status,
                        stage='',
                        disbursement_status='',
                        message=get_disbursement_response_message,
                        utr='')
                    disbursement_updated = await database.execute(query)
                    print(' value is not there', get_disbursement_response_message)
        return disbursement_array
    except Exception as e:
        log_id = await insert_logs('MYSQL', 'DB', 'GET-PENDING-CUSTOMERS', '500', {e.args[0]},
                                   datetime.now())
        result = JSONResponse(status_code=500, content={"message": f"Error Occurred at DB level - {e.args[0]}"})
# @router.post("/nac-sanction-status", status_code=status.HTTP_200_OK, tags=["Perdix"])
# async def pending_mandate_status(x_token: str = Depends(get_token_header), database: Database = Depends(get_database)
#                                  ):
#     try:
#         # perdix_customer_array = await get_pending_customers()
#         # for items in perdix_customer_array:
#             # update_perdix_customer = await update_perdix_status(items[1], items[6], items[11], 'fake-super-secret-token')
#
#         result = {"Success": "Mandates Updated"}
#     except Exception as e:
#         log_id = await insert_logs('MYSQL', 'DB', 'UPDATE-SOURCE-STATUS', '500', {e.args[0]},
#                                    datetime.now())
#         result = JSONResponse(status_code=500, content={"message": f"Error Occurred at DB level - {e.args[0]}"})
#     return result


# async def update_pending_customers(src_id, mandate_id, mandate_status, customer_id):
#     try:
#         database = get_database()
#         query = perdix_customer.update().where(perdix_customer.c.source_id == src_id).values(mandate_id=mandate_id,
#                                                                                              mandate_status=mandate_status,
#                                                                                              lotuspay_customer_id=customer_id,
#                                                                                              pending=0)
#         customer_updated = await database.execute(query)
#         return customer_updated
#     except Exception as e:
#         log_id = await insert_logs('MYSQL', 'DB', 'UPDATE-PENDING-CUSTOMERS', '500', {e.args[0]},
#                                    datetime.now())
#         result = JSONResponse(status_code=500, content={"message": f"Error Occurred at DB level - {e.args[0]}"})