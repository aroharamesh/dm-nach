import json
import urllib.request
from collections import defaultdict
from datetime import datetime
from fastapi import APIRouter, Depends, status, Request, Response, Body
from fastapi.responses import JSONResponse
from dm_nac_service.routes.dedupe import create_dedupe, find_dedupe
from dm_nac_service.data.database import get_database, sqlalchemy_engine, insert_logs
from dm_nac_service.gateway.nac_perdix_automator import perdix_post_login, perdix_fetch_loan, perdix_update_loan
from dm_nac_service.gateway.nac_sanction import nac_sanction, nac_get_sanction
from dm_nac_service.routes.sanction import create_sanction, find_sanction, sanction_status, find_loan_id_from_sanction
from dm_nac_service.resource.generics import response_to_dict
from dm_nac_service.data.sanction_model import sanction
from dm_nac_service.commons import get_env_or_fail
from dm_nac_service.app_responses.sanction import sanction_response_rejected_server, sanction_response_eligible, sanction_response_rejected_bureau, sanction_response_rejected_bre
from dm_nac_service.routes.disbursement import find_customer_sanction, create_disbursement
from dm_nac_service.gateway.nac_disbursement import nac_disbursement, disbursement_get_status
from dm_nac_service.data.disbursement_model import (disbursement)
from dm_nac_service.data.sanction_model import (sanction)
router = APIRouter()


NAC_SERVER = 'northernarc-server'


@router.post("/nac-dedupe-automator-data", status_code=status.HTTP_200_OK, tags=["Automator"])
async def post_automator_data(
    # request_info: Request,
    # response: Response

    # Below is to test manually by providing json data in request body
    request_info: dict = Body(...),

):
    """Function which prepares user data and posts"""
    try:
        print('*********************************** DATA FROM PERDIX THROUGH AUTOMATOR ***********************************')
        # payload = await request_info.json()

        # Below is for data published manually
        payload = request_info
        # print('data from post automator data', payload)

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

        # Fetch loan id from DB
        fetch_dedupe_info = await find_dedupe(sm_loan_id)
        print('13 - extracting loan information from Perdix', fetch_dedupe_info)

        # Condition to check the success and failure case
        # sm_loan_id = 287
        is_dedupe_present = fetch_dedupe_info.get('isDedupePresent', '')
        is_eligible_flag = fetch_dedupe_info.get('isEligible', '')
        str_fetch_dedupe_info = fetch_dedupe_info.get('dedupeRefId', '')

        # print('priting dedupe reference id ', str_fetch_dedupe_info)
        if(is_dedupe_present == 'False'):
            print('is eligible none', is_eligible_flag)
            message_remarks = ''
            update_loan_info = await update_loan('DEDUPE', sm_loan_id, str_fetch_dedupe_info, 'Dedupe', message_remarks,
                                                 'PROCEED', message_remarks)
            print('14 - updated loan information with dedupe reference to Perdix', update_loan_info)
        else:
            print('is eligible not none', is_eligible_flag)
            if(is_eligible_flag != '0'):
                message_remarks = fetch_dedupe_info.get('message')
                update_loan_info = await update_loan('DEDUPE', sm_loan_id, str_fetch_dedupe_info, 'Complete', message_remarks,
                                                     'PROCEED', message_remarks)
                print('14 - updated loan information with dedupe reference to Perdix', update_loan_info)
            else:
                message_remarks = fetch_dedupe_info.get('message')
                update_loan_info = await update_loan('DEDUPE', sm_loan_id, str_fetch_dedupe_info, 'Rejected',
                                                     message_remarks,
                                                     'PROCEED', message_remarks)
                print('14 - updated loan information with dedupe reference to Perdix', update_loan_info)
        # Posting the loan id to the Perdix API
        # Fake loan id
        # sm_loan_id = 287
        fetch_loan_info = await perdix_fetch_loan(sm_loan_id)
        # print('13 - extracting loan information from Perdix', fetch_loan_info)
        payload['partnerHandoffIntegration']['status'] = 'SUCCESS'
        payload['partnerHandoffIntegration']['partnerReferenceKey'] = str_fetch_dedupe_info
        #  Sending Response back to Perdix Automator
        # result = {
        #     "partnerHandoffIntegration": {
        #         "status": "SUCCESS",
        #         "partnerReferenceKey": str_fetch_dedupe_info
        #     }
        # }
        result = payload
        # Updating Dedupe Reference ID to Perdix API
        # str_fetch_dedupe_info = str(fetch_dedupe_info)

        return result
    except Exception as e:
        print(e)
        log_id = await insert_logs('MYSQL', 'DB', 'NA', '500', {e.args[0]},
                                   datetime.now())
        result = JSONResponse(status_code=500, content={"message": f"Issue with Northern Arc API, {e.args[0]}"})


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

        # Get Dedupe Reference ID
        # sm_loan_id = 287
        # print('before loan fetch')
        # fetch_dedupe_info = await find_dedupe(sm_loan_id)
        # dedupe_reference_id = "5134610851082868"
        # print(fetch_dedupe_info)


        customer_data = payload["enrollmentDTO"]["customer"]
        loan_data = payload["loanDTO"]["loanAccount"]
        first_name = customer_data.get("firstName", "")
        middle_name = customer_data.get("", "Dummy")
        last_name = customer_data.get("", "Dummy")
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
        sm_loan_id = loan_data.get("id", "SML00253011")
        udhyog_aadhar = customer_data.get("aadhaarNo")
        pan_no = customer_data.get("panNo", "ALWPG5909L")
        bank_accounts_info = {}
        if len(customer_data["customerBankAccounts"]) > 0:
            bank_accounts_info = customer_data["customerBankAccounts"][0]
        account_number = bank_accounts_info.get("accountNumber", "1234313323")
        customer_bank_name = bank_accounts_info.get("customerBankName", "YES BANK LIMITED")
        owned_vehicle = customer_data.get("","2W")
        curr_door_number = customer_data.get("doorNo", "jayanagar201")
        curr_locality = customer_data.get("locality", "bangalore")
        landmark = customer_data.get("","banashankari circle")
        curr_district = customer_data.get("district","bangalore")
        # curr_city=customer_data.get("","bangalore")
        curr_state = customer_data.get("state","Karnataka")
        occupation_info = {}

        if len(customer_data["familyMembers"]) > 0:
            occupation_info = customer_data["familyMembers"][0]
        curr_occupation = occupation_info.get("occupation", "SALARIED_OTHER")
        mode_salary = occupation_info.get("", "ONLINE")
        installment_info = {}
        if len(loan_data["disbursementSchedules"]) > 0:
            installment_info = loan_data["disbursementSchedules"][0]
        installment_date = installment_info.get("", "2020-04-11")
        income_info = {}
        if len(customer_data["familyMembers"]) > 0:
            income_info = customer_data["familyMembers"][0]["incomes"][0]
        gross_income = income_info.get("incomeEarned", 30000)
        net_income = income_info.get("incomeEarned", 40000)
        loan_purpose = loan_data.get("requestedLoanPurpose","Others-TO BUY GOLD")
        loan_amount = loan_data.get("loanAmount","10000")
        interest_rate = loan_data.get("interestRate","25")
        schedule_date = loan_data.get("scheduleStartDate", "")

        if "str" != type(schedule_date).__name__:
            schedule_date = "{:04d}-{:02d}-{:02d}".format(
                schedule_date["year"],
                schedule_date["monthValue"],
                schedule_date["dayOfMonth"],
            )

        process_fee = loan_data.get("processingFeeInPaisa", 900)
        pre_emi = loan_data.get("", 0)
        max_emi = loan_data.get("emi", 100)
        gst = loan_data.get("",0)

        emi_info = {}
        if len(customer_data["liabilities"]) > 0:
            emi_info = customer_data["liabilities"][0]
        emi_date = emi_info.get("", "2022-04-10")
        repayment_frequency = payload.get("frequency", "WEEKLY")

        repayment_frequency = "Monthly" if repayment_frequency == "Monthly" else "F"
        repayment_frequency = loan_data.get("frequencyRequested","WEEKLY")
        tenure_value = loan_data.get("tenure", 36)
        tenure_value_int = int(tenure_value)

        product_name = loan_data.get("productCode", "Personal Loan")
        email_id = customer_data.get("email", "testsm1@gmail.com")
        maritual_status = customer_data.get("maritalStatus", "MARRIED")
        client_id = loan_data.get("customerId", "12345")

        repayment_info = {}
        if len(customer_data["verifications"]) > 0:
            repayment_info = customer_data["verifications"][0]

        repayment_mode = repayment_info.get("", "NACH")

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
                "currLandmark": landmark,
                "currCity": "",
                "currDistrict": curr_district,
                "currState": curr_state,
                "currPincode": pincode,
                "permDoorAndBuilding": curr_door_number,
                "permLandmark": landmark,
                "permCity":"",
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
                "tenureUnits": "",
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
        print('COMING HERE')
        print('1 - Sanction Data from Perdix and Sending the data to create sanction function', sanction_data)
        sanction_response = await create_sanction(sanction_data)
        print('100 - response back from NAC ', sanction_response)

        get_sanction_ref = await find_sanction(sm_loan_id)
        print('101 - FOUND CUSTOMER ID FROM DB', get_sanction_ref)
        reference_id = get_sanction_ref.get('customerId', '')
        print('printing referece id ', reference_id)
        message_remarks = 'testing '

        # To Update Perdix with Sanction Reference ID
        update_loan_info = await update_loan('SANCTION', sm_loan_id, reference_id, 'Dedupe', message_remarks,
                                             'PROCEED', message_remarks)



        payload['partnerHandoffIntegration']['status'] = 'SUCCESS'
        payload['partnerHandoffIntegration']['partnerReferenceKey'] = reference_id
        # print('14 - updated loan information with dedupe reference to Perdix', update_loan_info)
        # update_loan_info = await update_loan(sm_loan_id, str_fetch_dedupe_info, 'Dedupe', message_remarks,
        #                                      'PROCEED', message_remarks)
        # print('0 - testing', sanction_response)
        # print('1 - Prepare Data to push to NAC endpoint', sanction_data)
        # return sanction_data

        return payload
    except Exception as e:
        print(e)


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
    # result = loan_info

    #  For testing manually
    # loan_update_response = await perdix_update_loan(loan_info)
    # result = loan_update_response

    # For Real updating the loan information
    get_loan_info = await perdix_fetch_loan(loan_id)
    # print('get loan info', get_loan_info)
    # print('Reject Reason - ', get_loan_info.get('loanAccount').get('rejectReason'))
    # print('Stage - ', get_loan_info.get('stage'))
    # print('Remarks - ', get_loan_info.get('remarks'))
    # print('loanProcessAction - ', get_loan_info.get('loanProcessAction'))
    # print('udf41 - ', get_loan_info.get('accountUserDefinedFields').get('userDefinedFieldValues').get('udf41'))
    json_data_version = get_loan_info.get('version')
    # print('printing version of data ', json_data_version)
    if "rejectReason" in get_loan_info:
        get_loan_info['rejectReason'] = reject_reason
    # if "stage" in get_loan_info:
    #     get_loan_info['stage'] = "Testing stage"
    get_loan_info['stage'] = stage
    if "remarks1" in get_loan_info:
        get_loan_info['remarks1'] = "Testing remarks1"
    if "loanProcessAction" in get_loan_info:
        get_loan_info['loanProcessAction'] = "Testing loanProcessAction"
    if "accountUserDefinedFields" in get_loan_info:
        if(url_type == 'DEDUPE'):
            # get_loan_info['accountUserDefinedFields']['userDefinedFieldValues'] = {
            #     'udf41': reference_id
            #     # 'udf42': "5211201547885960"
            #     # 'udf43': "5211201547885960"
            #     # 'udf44': "5211201547885960"
            #     # 'udf45': "5211201547885960"
            # }
            # get_loan_info['accountUserDefinedFields'] = {
            #     'userDefinedFieldValues': {
            #         'udf41': reference_id
            #     }
            # }
            get_loan_info['accountUserDefinedFields']['userDefinedFieldValues']['udf41'] = reference_id

            # print('dedupe', get_loan_info)
        if(url_type == 'SANCTION'):
            # get_loan_info['accountUserDefinedFields']['userDefinedFieldValues'] = {
            #     'udf42': reference_id
            #     # 'udf42': "5211201547885960"
            #     # 'udf43': "5211201547885960"
            #     # 'udf44': "5211201547885960"
            #     # 'udf45': "5211201547885960"
            # }
            # get_loan_info['accountUserDefinedFields'] = {
            #     'userDefinedFieldValues': {
            #         'udf42': reference_id
            #     }
            # }
            get_loan_info['accountUserDefinedFields']['userDefinedFieldValues']['udf42'] = reference_id
            # print('sanction', get_loan_info)
        if(url_type == 'SANCTION-REFERENCE'):
            # get_loan_info['accountUserDefinedFields']['userDefinedFieldValues'] = {
            #     'udf42': reference_id
            #     # 'udf42': "5211201547885960"
            #     # 'udf43': "5211201547885960"
            #     # 'udf44': "5211201547885960"
            #     # 'udf45': "5211201547885960"
            # }
            # get_loan_info['accountUserDefinedFields'] = {
            #     'userDefinedFieldValues': {
            #         'udf42': reference_id
            #     }
            # }
            get_loan_info['accountUserDefinedFields']['userDefinedFieldValues']['udf43'] = reference_id
            # print('sanction', get_loan_info)
        if(url_type == 'DISBURSEMENT'):
            # get_loan_info['accountUserDefinedFields']['userDefinedFieldValues'] = {
            #     'udf42': reference_id
            #     # 'udf42': "5211201547885960"
            #     # 'udf43': "5211201547885960"
            #     # 'udf44': "5211201547885960"
            #     # 'udf45': "5211201547885960"
            # }
            # get_loan_info['accountUserDefinedFields'] = {
            #     'userDefinedFieldValues': {
            #         'udf42': reference_id
            #     }
            # }
            get_loan_info['accountUserDefinedFields']['userDefinedFieldValues']['udf44'] = reference_id
            # print('sanction', get_loan_info)
        if (url_type == 'DISBURSEMENT-ITR'):
            # get_loan_info['accountUserDefinedFields']['userDefinedFieldValues'] = {
            #     'udf42': reference_id
            #     # 'udf42': "5211201547885960"
            #     # 'udf43': "5211201547885960"
            #     # 'udf44': "5211201547885960"
            #     # 'udf45': "5211201547885960"
            # }
            # get_loan_info['accountUserDefinedFields'] = {
            #     'userDefinedFieldValues': {
            #         'udf42': reference_id
            #     }
            # }
            get_loan_info['accountUserDefinedFields']['userDefinedFieldValues']['udf45'] = reference_id
            # print('sanction', get_loan_info)
    # if "version" in get_loan_info:
    #     get_loan_info['version'] = json_data_version + 2

    prepare_loan_info = {
        "loanAccount": get_loan_info,
        "loanProcessAction": loan_process_action,
        "stage": stage,
        "remarks": remarks
    }
    print('prepare_loan_info - ', prepare_loan_info)
    update_perdix_loan = await perdix_update_loan(prepare_loan_info)
    # update_perdix_loan_dict = response_to_dict(update_perdix_loan)
    # update_perdix_loan_dict = json.loads(update_perdix_loan.decode('utf-8'))
    # print('coming after gateway ', update_perdix_loan)


    # loan_update_response = await perdix_update_loan(loan_id)

    # result = get_loan_info
    result = update_perdix_loan

    # print('loan status code ', loan_update_response.status_code)
    # print('loan status content ')
    # print(result)
    # get_perdix_loan_data = await perdix_fetch_loan(loan_id)
    # print('getting customer', get_perdix_data)

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