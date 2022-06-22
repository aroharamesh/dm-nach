import requests


def perdix_login(settings):
    data = "client_id=application&client_secret=mySecretOAuthSecret&grant_type=password&password={}&scope=read+write&skip_relogin=yes&username={}"
    login_url = settings.perdix_base_url + "oauth/token"
    login_resp = requests.post(
        login_url,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        params={"cacheBuster": "1648217318664"},
        data=data.format(settings.perdix_password, settings.perdix_username),
    )
    login_resp_json = login_resp.json()
    return login_resp_json


def perdix_enrollment_get(payload, settings, headers, token):
    customer_id = payload["enrollmentDTO"]["customer"]["id"]
    enrollment_url = settings.perdix_base_url + "api/enrollments/" + str(customer_id)
    customer = requests.request(
        "GET", enrollment_url, headers={**headers, "Authorization": "Bearer " + token}
    ).json()
    return customer


def perdix_enrollment_update(customer_data, settings, headers, token, action="PROCEED"):
    enrollment_url = settings.perdix_base_url + "api/enrollments/"
    customer_save = {"customer": customer_data, "enrollmentAction": action}
    customer = requests.request(
        "PUT",
        enrollment_url,
        headers={**headers, "Authorization": "Bearer " + token},
        json=customer_save,
    ).json()
    return customer


def perdix_loan_get(payload, settings, headers, token):
    loan_id = payload["loanDTO"]["loanAccount"]["id"]
    loan_url = settings.perdix_base_url + "api/individualLoan/" + str(loan_id)
    loan_data = requests.request(
        "GET", loan_url, headers={**headers, "Authorization": "Bearer " + token}
    ).json()
    return loan_data


def perdix_loan_update(loan_data, settings, headers, token, action="SAVE"):
    loan_post_url = settings.perdix_base_url + "api/individualLoan/"
    loan_save = {"loanAccount": loan_data, "loanProcessAction": action}
    loan_save_resp = requests.request(
        "POST",
        loan_post_url,
        headers={**headers, "Authorization": "Bearer " + token},
        json=loan_save,
    ).json()
    return loan_save_resp
