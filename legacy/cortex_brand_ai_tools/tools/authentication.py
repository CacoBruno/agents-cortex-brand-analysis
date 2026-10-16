import requests


def get_auth_headers(auth_endpoint, credentials):

    response = requests.post(auth_endpoint, json=credentials)
    response_json = response.json()

    auth_headers = {
        "x-authorization-user-id": response_json["userId"],
        "x-authorization-token": response_json["key"],
    }

    return {"status_code": response.status_code, "auth_headers": auth_headers}
