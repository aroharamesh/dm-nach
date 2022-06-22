from pydantic import BaseSettings


class Settings(BaseSettings):
    user_url: str
    loan_url: str
    repayment_url: str
    user_document_upload_url: str
    loan_document_upload_url: str
    disbursement_status_url: str
    file_stream_url: str
    username: str
    password: str
    underwriting_engine_login_url: str
    underwriting_engine_username: str
    underwriting_engine_password: str
    underwriting_engine_calc_url: str
    perdix_username: str
    perdix_password: str
    perdix_base_url: str
    perdix_form_url: str

    class Config:
        env_file = "arthmate_lender_handoff_service/.env"
        env_file_encoding = "utf-8"
