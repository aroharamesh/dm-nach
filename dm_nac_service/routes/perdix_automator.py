
from fastapi import APIRouter, Depends, status, Request, Response, Body
from dm_nac_service.routes.dedupe import create_dedupe


router = APIRouter()


@router.post("/nac-dedupe-automator-data", status_code=status.HTTP_200_OK)
async def post_automator_data(
    request_info: Request,
    response: Response

    # Below is to test manually by providing json data in request body
    # request_info: dict = Body(...),

):
    """Function which prepares user data and posts"""
    try:
        payload = await request_info.json()

        # Below is for data published manually
        # payload = request_info

        customer_data = payload["enrollmentDTO"]["customer"]
        loan_data = payload["loanDTO"]["loanAccount"]
        first_name = customer_data.get("firstName", "")
        middle_name = customer_data.get("middleName", "")
        last_name = customer_data.get("lastName", "")
        first_name = first_name if first_name else ""
        last_name = last_name if last_name else ""
        middle_name = middle_name if middle_name else ""
        full_name = f"{first_name} {middle_name} {last_name}"
        print(f"-------full_name--------{full_name}")
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
        dedupe_data = [
            {
                "accountNumber": account_number,
                "contactNumber": mobile_number,
                "customerName": first_name,
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
        ]
        dedupe_response = await create_dedupe(dedupe_data)
        return dedupe_data
    except Exception as e:
        print(e)



@router.post("/nac-sanction-automator-data", status_code=status.HTTP_200_OK)
async def post_sanction_automator_data(
    # request_info: Request,
    # response: Response
    # Below is to test manually by providing json data in request body
    request_info: dict = Body(...),
):
    """Function which prepares user data and posts"""
    try:
        print("coming inside prepare sanction data")
        # payload = await request_info.json()
        # Below is for data published manually
        payload = request_info
        customer_data = payload["enrollmentDTO"]["customer"]
        loan_data = payload["loanDTO"]["loanAccount"]
        first_name = customer_data.get("firstName", "")
        middle_name = customer_data.get("middleName", "")
        last_name = customer_data.get("lastName", "")
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
        owned_vehicle=customer_data.get("","2W")
        curr_door_number = customer_data.get("doorNo", "jayanagar201")
        curr_locality=customer_data.get("locality", "bangalore")
        landmark=customer_data.get("","banashankari circle")
        curr_district=customer_data.get("district","bangalore")
        # curr_city=customer_data.get("","bangalore")
        curr_state=customer_data.get("state","Karnataka")
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
        gross_income= income_info.get("incomeEarned", 30000)
        net_income=income_info.get("incomeEarned", 40000)
        loan_purpose=loan_data.get("requestedLoanPurpose","Others-TO BUY GOLD")
        loan_amount=loan_data.get("loanAmount","10000")
        interest_rate=loan_data.get("interestRate","25")
        schedule_date = loan_data.get("scheduleStartDate", "")
        if "str" != type(schedule_date).__name__:
            schedule_date = "{:04d}-{:02d}-{:02d}".format(
                schedule_date["year"],
                schedule_date["monthValue"],
                schedule_date["dayOfMonth"],
            )
        process_fee=loan_data.get("processingFeeInPaisa", 900)
        pre_emi=loan_data.get("", 0)
        max_emi=loan_data.get("emi", 100)
        gst=loan_data.get("",0)
        emi_info = {}
        if len(customer_data["liabilities"]) > 0:
            emi_info = customer_data["liabilities"][0]
        emi_date = emi_info.get("", "2022-04-10")
        repayment_frequency = payload.get("frequency", "WEEKLY")
        repayment_frequency = "Monthly" if repayment_frequency == "Monthly" else "F"
        repayment_frequency=loan_data.get("frequencyRequested","WEEKLY")
        tenure_value = loan_data.get("tenure", 36)
        product_name = loan_data.get("productCode", "Personal Loan")
        email_id = customer_data.get("email", "testsm1@gmail.com")
        maritual_status = customer_data.get("maritalStatus", "MARRIED")
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
                "tenureValue": int(tenure_value),
                "tenureUnits": "",
                "productName": product_name,
                "primaryBankAccount": account_number,
                "bankName": customer_bank_name,
                "modeOfSalary": mode_salary,
                "clientId": "",
                "dedupeReferenceId": "",
                "email": email_id,
                "middleName": middle_name,
                "maritalStatus": maritual_status,
                "loanId": str(sm_loan_id),
                }
        # print(sanction_data)
        return sanction_data
        # sanction_response = await create_sanction(sanction_data)
        # return sanction_data
    except Exception as e:
        print(e)