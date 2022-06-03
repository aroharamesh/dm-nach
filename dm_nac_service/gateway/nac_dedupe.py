from datetime import datetime
import requests
from dm_nac_service.resource.generics import response_to_dict
from fastapi.responses import JSONResponse
from dm_nac_service.data.database import insert_logs
from dm_nac_service.commons import get_env_or_fail
import json

NAC_SERVER = 'northernarc-server'


async def nac_dedupe(context, data):
    """ Generic Post Method for dedupe """
    try:
        validate_url = get_env_or_fail(NAC_SERVER, 'base-url', NAC_SERVER + ' base-url not configured')
        api_key = get_env_or_fail(NAC_SERVER, 'api-key', NAC_SERVER + ' api-key not configured')
        group_key = get_env_or_fail(NAC_SERVER, 'group-key', NAC_SERVER + ' group-key not configured')
        originator_id = get_env_or_fail(NAC_SERVER, 'originator-id', NAC_SERVER + 'originator ID not configured')
        sector_id = get_env_or_fail(NAC_SERVER, 'sector-id', NAC_SERVER + 'Sector ID not configured')
        url = validate_url + f'/{context}?originatorId={originator_id}&sectorId={sector_id}'
        str_url = str(url)
        str_data = data.dict()
        headers = {
            "API-KEY": api_key,
            "GROUP-KEY": group_key,
            "Content-Type": "application/json",
            "Content-Length": "0",
            "User-Agent": 'My User Agent 1.0',
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

        get_root = str_data.get('__root__')
        str_get_root = str(get_root)

        dedupe_context_response = requests.post(url, json=get_root, headers=headers)

        if(dedupe_context_response.status_code == 200):
            response_content = dedupe_context_response.content
            res = json.loads(response_content.decode('utf-8'))
            dedupe_context_response_id = res[0]['dedupeReferenceId']
            # result = dedupe_context_response_id
            result = res[0]
        else:
            dedupe_context_dict = response_to_dict(dedupe_context_response)
            log_id = await insert_logs('NAC', 'NAC', get_root, dedupe_context_response.status_code,
                                   dedupe_context_dict, datetime.now())
            result = {"error": "Error Creating the Dedupe"}
    except Exception as e:
        log_id = await insert_logs('NAC', 'NAC', str_get_root, dedupe_context_response.status_code, dedupe_context_response.content, datetime.now())
        result = JSONResponse(status_code=500, content={"message": f"Error Occurred at Northern Arc Post Method - {e.args[0]}"})

    return result