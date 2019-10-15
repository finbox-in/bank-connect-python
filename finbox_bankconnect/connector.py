import requests
import finbox_bankconnect
from finbox_bankconnect.custom_exceptions import ServiceTimeOutError, InvalidBankNameError
from finbox_bankconnect.custom_exceptions import PasswordIncorrectError, UnparsablePDFError
from finbox_bankconnect.custom_exceptions import FileProcessFailedError, EntityNotFoundError
from finbox_bankconnect.custom_exceptions import CannotIdentityBankError

def get_progress_status(progress):
    for statement in progress:
        if statement["status"] in ["failed", "processing"]:
            return statement["status"]
    return "completed"

def create_entity(link_id):
    url = "{}/bank-connect/{}/entity/".format(finbox_bankconnect.base_url, finbox_bankconnect.api_version)
    headers = { 'x-api-key': finbox_bankconnect.api_key }
    data = { 'link_id': link_id }

    entity_id = None
    response = None

    retry_left = finbox_bankconnect.max_retry_limit
    while retry_left:
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 201:
            try:
                entity_id = response.json()['entity_id']
                break
            except KeyError:
                pass
        retry_left -= 1
    if entity_id is None:
        #TODO: Log here
        raise ServiceTimeOutError
    return entity_id

def get_link_id(entity_id):
    url = "{}/bank-connect/{}/entity/{}/".format(finbox_bankconnect.base_url, finbox_bankconnect.api_version, entity_id)
    headers = { 'x-api-key': finbox_bankconnect.api_key }

    got_link_id = False
    link_id = None
    response = None

    retry_left = finbox_bankconnect.max_retry_limit
    while retry_left:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            try:
                link_id = response.json()['link_id']
                got_link_id = True
                break
            except KeyError:
                pass
        elif response.status_code == 404:
            raise EntityNotFoundError
        retry_left -= 1
    if not got_link_id:
        #TODO: Log here
        raise ServiceTimeOutError
    return link_id

def upload_file(entity_id, file_obj, pdf_password, bank_name):
    api_name = 'upload'
    data = dict()
    if bank_name is None:
        api_name = 'bankless_upload'
    else:
        data['bank_name'] = bank_name
    if entity_id is not None:
        data['entity_id'] = entity_id
    if pdf_password is not None:
        data['pdf_password'] = pdf_password

    url = "{}/bank-connect/{}/statement/{}/?identity=true".format(finbox_bankconnect.base_url, finbox_bankconnect.api_version, api_name)
    headers = { 'x-api-key': finbox_bankconnect.api_key }
    files = { 'file': file_obj }
    response = None

    retry_left = finbox_bankconnect.max_retry_limit
    while retry_left:
        response = requests.post(url, headers=headers, data=data, files=files)
        if response.status_code == 200:
            response = response.json()
            try:
                is_authentic = not response['is_fraud']
                entity_id = response['entity_id']
                identity = response['identity']
                return is_authentic, entity_id, identity
            except KeyError:
                pass
        elif response.status_code == 400:
            response = response.json()
            # check for invalid bank_name
            if response.get('bank_name') is not None:
                raise InvalidBankNameError
            message = response.get('message')
            if message is not None:
                #TODO: instead of string matching and message, add status code checks
                if message == "Password incorrect":
                    raise PasswordIncorrectError
                elif message == "PDF is not parsable":
                    raise UnparsablePDFError
                elif message == "Unable to detect bank. Please provide BANK NAME.":
                    raise CannotIdentityBankError
                else:
                    raise FileProcessFailedError
        retry_left -= 1
    #TODO: log here the response
    raise ServiceTimeOutError

def get_transactions(entity_id):
    url = "{}/bank-connect/{}/entity/{}/transactions/".format(finbox_bankconnect.base_url, finbox_bankconnect.api_version, entity_id)
    headers = { 'x-api-key': finbox_bankconnect.api_key }
    response = requests.get(url, headers=headers)
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
    response = requests.get(url, headers=headers)
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
    response = requests.get(url, headers=headers)
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

def get_salary(entity_id):
    url = "{}/bank-connect/{}/entity/{}/salary/".format(finbox_bankconnect.base_url, finbox_bankconnect.api_version, entity_id)
    headers = { 'x-api-key': finbox_bankconnect.api_key }
    response = requests.get(url, headers=headers)
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

def get_recurring(entity_id):
    url = "{}/bank-connect/{}/entity/{}/recurring_transactions/".format(finbox_bankconnect.base_url, finbox_bankconnect.api_version, entity_id)
    headers = { 'x-api-key': finbox_bankconnect.api_key }
    response = requests.get(url, headers=headers)
    if response.status_code == 404:
        return "not_found", None, None, None, None
    elif not response.status_code == 200:
        #TODO: log here the response
        return "service_failed", None, None, None, None
    response = response.json()
    try:
        status = get_progress_status(response['progress'])
        if status == "completed":
            accounts = response['accounts']
            fraud_info = response['fraud']['fraud_type']
            credit_recurring = response['transactions'].get("credit_transactions", [])
            debit_recurring = response['transactions'].get("debit_transactions", [])
            return status, accounts, fraud_info, credit_recurring, debit_recurring
    except KeyError:
        #TODO: log here the response
        return "format_changed", None, None, None, None
    return status, None, None, None, None

def get_lender_transactions(entity_id):
    url = "{}/bank-connect/{}/entity/{}/lender_transactions/".format(finbox_bankconnect.base_url, finbox_bankconnect.api_version, entity_id)
    headers = { 'x-api-key': finbox_bankconnect.api_key }
    response = requests.get(url, headers=headers)
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
