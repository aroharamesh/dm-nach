import requests
import logging
import json

logger = logging.getLogger("arthmate-lender-handoff-service")

URL = (
    "http://localhost/management/server-ext/external_interface_logger.php?source=system"
)


def log(source, type, ref, txn, req, resp, status, error_desc):

    success = status < 400
    response = resp.json() if success else resp
    payload = {
        "service_provider": source,
        "service_type": type,
        "reference_id": ref,
        "transaction_id": txn,
        "enquiry_request_string": f"{req}",
        "enquiry_response_string": f"{response}",
        "status": "Success" if success else "Failed",
        "https_status_code": status,
        "error_code": "Failed" if not success else None,
        "error_description": error_desc if not success else None,
        "processing_status": "PROCESSED",
    }

    try:
        requests.post(
            url=URL,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )
    except Exception as ex:
        logger.info(f"payload: {payload} Error Occurred: {ex}")
