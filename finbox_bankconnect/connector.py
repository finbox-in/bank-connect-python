import requests
import finbox_bankconnect

def get_progress_status(progress):
    for statement in progress:
        if statement["status"] in ["failed", "processing"]:
            return statement["status"]
    return "completed"

def create_entity(link_id):
    pass

def get_link_id(entity_id):
    pass

def upload_file(entity_id, file_obj, bank_name):
    pass

def get_transactions(entity_id):
    url = "{}/bank-connect/{}/entity/{}/transactions/".format(finbox_bankconnect.base_url, finbox_bankconnect.api_version, entity_id)
    headers = { 'x-api-key': finbox_bankconnect.api_key }
    response = requests.request("GET", url, headers=headers)
    if response.status_code == 404:
        return "not_found", None, None, None
    elif not response.status_code == 200:
        #TODO: log here the response
        return "service_failed", None, None, None
    response = response.json()
    try:
        status = get_progress_status(response['progress'])
        if status == "completed":
            accounts = response['accounts']
            fraud_info = response['fraud']['fraud_type']
            transactions = response['transactions']
            return status, accounts, fraud_info, transactions
    except KeyError:
        #TODO: log here the response
        return "format_changed", None, None, None
    return status, None, None, None


def get_identity(entity_id):
    url = "{}/bank-connect/{}/entity/{}/identity/".format(finbox_bankconnect.base_url, finbox_bankconnect.api_version, entity_id)
    headers = { 'x-api-key': finbox_bankconnect.api_key }
    response = requests.request("GET", url, headers=headers)
    if response.status_code == 404:
        return "not_found", None, None, None
    elif not response.status_code == 200:
        #TODO: log here the response
        return "service_failed", None, None, None
    response = response.json()
    try:
        status = get_progress_status(response['progress'])
        if status == "completed":
            accounts = response['accounts']
            fraud_info = response['fraud']['fraud_type']
            identity = response['identity'][0]
            return status, accounts, fraud_info, identity
    except KeyError:
        #TODO: log here the response
        return "format_changed", None, None, None
    return status, None, None, None

def get_accounts(entity_id):
    url = "{}/bank-connect/{}/entity/{}/accounts/".format(finbox_bankconnect.base_url, finbox_bankconnect.api_version, entity_id)
    headers = { 'x-api-key': finbox_bankconnect.api_key }
    response = requests.request("GET", url, headers=headers)
    if response.status_code == 404:
        return "not_found", None, None
    elif not response.status_code == 200:
        #TODO: log here the response
        return "service_failed", None, None
    response = response.json()
    try:
        status = get_progress_status(response['progress'])
        if status == "completed":
            accounts = response['accounts']
            fraud_info = response['fraud']['fraud_type']
            return status, accounts, fraud_info
    except KeyError:
        #TODO: log here the response
        return "format_changed", None, None
    return status, None, None
