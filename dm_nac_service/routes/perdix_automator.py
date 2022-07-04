
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
