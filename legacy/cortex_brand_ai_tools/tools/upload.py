import json
import sys
import traceback
from io import StringIO
from time import sleep

import requests

LOADMANAGER = "https://api.cortex-intelligence.com"

DATA_PARSER = {
    "charset": "UTF-8",
    "quote": '"',
    "escape": "\\",
    "delimiter": "\t",
    "fileType": "CSV",
    "encode": "UTF-8",
}


def _status_check(endpoint, response):
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        message = f"""
        ------- _get_data_input Failed -------
        Endpoint: {endpoint}
        Status: {response.status_code}
        Error: {str(e)}
        """
        traceback.print_tb(exc_traceback)
        raise (message)
    return


def _get_sid_bearer_token(auth_endpoint, credentials):
    response = requests.post(auth_endpoint, json=credentials)
    _status_check(auth_endpoint, response)
    response_json = response.json()
    return {"Authorization": "Bearer " + response_json["key"]}


def _get_data_input(content, loadmanager, headers):
    endpoint = loadmanager + "/datainput"
    response = requests.post(endpoint, headers=headers, json=content)
    _status_check(endpoint, response)
    data_input_id = response.json()["id"]
    return data_input_id


def _get_execution_id(data_input_id, content, loadmanager, headers):
    endpoint = loadmanager + "/datainput/" + data_input_id + "/execution"
    response = requests.post(endpoint, headers=headers, json=content)
    _status_check(endpoint, response)
    execution_id = response.json()["executionId"]
    return execution_id


def _start_process(execution_id, loadmanager, headers):
    endpoint = loadmanager + "/execution/" + execution_id + "/start"
    response = requests.put(endpoint, headers=headers)
    _status_check(endpoint, response)
    return


def _send_files(files, endpoint, headers, data_parser):

    response = requests.post(
        endpoint, headers=headers, data=data_parser, files={"file": files}
    )
    _status_check(endpoint, response)
    return


def _execution_history(execution_id, loadmanager, headers):
    endpoint = loadmanager + "/execution/" + execution_id
    response = requests.get(endpoint, headers=headers)
    _status_check(endpoint, response)
    return response


def upload_to_ctx(
    files,
    cubo_id,
    ctx_auth_endpoint,
    ctx_credentials,
    ignoreValidationErrors=True,
    fileProcessingTimeout=1200,
    executionTimeout=1200,
    data_parser=DATA_PARSER,
    loadmanager=LOADMANAGER,
):

    # ================ Get Bearer Token ===================
    headers = _get_sid_bearer_token(ctx_auth_endpoint, ctx_credentials)

    # ================ Content ===================
    content = {
        "destinationId": cubo_id,
        "fileProcessingTimeout": fileProcessingTimeout,
        "executionTimeout": executionTimeout,
        "ignoreValidationErrors": ignoreValidationErrors,
    }

    # ================ Get Data Input Id ======================
    data_input_id = _get_data_input(content, loadmanager, headers)

    # ================ Get Execution Id =======================
    execution_id = _get_execution_id(data_input_id, content, loadmanager, headers)

    # ================ Make Endpoint ===========================
    endpoint = loadmanager + "/execution/" + execution_id + "/file"

    # ================ Send files ===========================
    if type(files) is list:
        list_of_files = files
    else:
        list_of_files = [files]

    for f in list_of_files:
        _send_files(f, endpoint, headers, data_parser)

    # ================ Start Data Input Process ===========================
    _start_process(execution_id, loadmanager, headers)

    # ================ Execution History  ================================
    n_seconds = 10
    upload_completed = False
    while not upload_completed:
        print("..waiting for upload to be done")
        sleep(n_seconds)
        execution_history = _execution_history(execution_id, loadmanager, headers)
        execution_history_dict = execution_history.json()
        upload_completed = execution_history_dict["completed"]

    if execution_history_dict["success"]:
        print("Upload to Cube Finished")
    else:
        print("Error on Upload to Cube")

    return execution_history_dict


