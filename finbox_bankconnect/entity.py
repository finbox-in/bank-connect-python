from collections import defaultdict
import time
from finbox_bankconnect.utils import is_valid_uuid4
import finbox_bankconnect.connector as connector
from finbox_bankconnect.custom_exceptions import ExtractionFailedError, EntityNotFoundError, ServiceTimeOutError
import finbox_bankconnect

class Entity:
    def __init__(self, source=None, entity_id=None, link_id=None):
        if source is None or not isinstance(source, str):
            raise ValueError("must create entity using get or create methods of Entity class")

        # basic identifiers
        self.__entity_id = entity_id
        self.__link_id = link_id

        # lists to keep track of accounts and fraud info
        self.__accounts = []
        self.__fraud_info = []

        # dictionary to keep track of identity info
        self.__identity = dict()

        # lists to keep track of different transactions
        self.__transactions = []
        self.__credit_recurring = []
        self.__debit_recurring = []
        self.__salary = []

        # lazy loading trackers
        self.__is_loaded = defaultdict(bool)

        # set default lazy loading values based on instance creation source
        if source == 'c' and link_id is not None:
            self.__is_loaded['link_id'] = True
        elif source == 'g':
            self.__is_loaded['entity_id'] = True

    @staticmethod
    def get(entity_id):
        """Creates an entity with given entity_id and returns the instance

        arguments:
        entity_id -- the entity id string (UUID version 4)
        """
        if not entity_id:
            raise ValueError("entity_id cannot be blank or None")
        if not isinstance(entity_id, str):
            raise ValueError("entity_id must be a string")
        if not is_valid_uuid4(entity_id):
            raise ValueError("invalid entity_id")
        return Entity(source='g', entity_id=entity_id)

    @staticmethod
    def create(link_id=None):
        """Creates an entity with the optional link_id and returns the instance

        arguments:
        link_id (optional) -- the link_id string
        """
        if link_id and not isinstance(link_id, str):
            raise ValueError("link_id must be a string")
        return Entity(source='c', link_id=link_id)

    @property
    def entity_id(self):
        """Returns the entity_id for the Entity instance"""
        if not self.__is_loaded['entity_id']:
            if self.__is_loaded['link_id']:
                # create an entity with the link_id and set it
                self.__entity_id = connector.create_entity(self.__link_id)
                self.__is_loaded['entity_id'] = True
            else:
                raise ValueError("no statement uploaded yet so use upload_statement method to set the entity_id")
        return self.__entity_id

    @property
    def link_id(self):
        """Returns the link_id for the Entity instance"""
        if not self.__is_loaded['link_id']:
            if self.__is_loaded['entity_id']:
                # fetch the link id for the entity id and set it
                self.__link_id = connector.get_link_id(self.__entity_id) # fetch link id for the given entity
                self.__is_loaded['link_id'] = True
            else:
                raise ValueError("no statement uploaded yet so use upload_statement method to set the link_id")
        return self.__link_id

    def upload_statement(self, file_path, pdf_password=None, bank_name=None):
        """Uploads the statement for the given entity instance, creates entity if required too
            if successfully uploaded, then returns a boolean indicating whether uploaded statement was
            authentic

        arguments:
        file_path -- path of the pdf file
        pdf_password (optional) -- pdf password string
        bank_name (optional) -- bank name string
        """
        if not file_path:
            raise ValueError("file_path cannot be blank or None")
        if not isinstance(file_path, str):
            raise ValueError("file_path must be a string")
        if not file_path.lower().endswith('.pdf'):
            raise ValueError("file_path must be of a pdf file")

        if pdf_password is not None and not isinstance(pdf_password, str):
            raise ValueError("pdf_password must be a string or None")

        if bank_name and not isinstance(bank_name, str):
            raise ValueError("bank_name must be a string or None")
        if bank_name == "":
            bank_name = None

        with open(file_path) as file_obj: #throws IOError if file is unaccessible or doesn't exists

            if self.__is_loaded['link_id'] and not self.__is_loaded['entity_id']:
                # create an entity with the link_id and set it
                self.__entity_id = connector.create_entity(self.__link_id)
                self.__is_loaded['entity_id'] = True

            is_authentic, entity_id, identity = connector.upload_file(self.__entity_id, file_obj, pdf_password, bank_name)
            if not self.__is_loaded['entity_id']:
                self.__entity_id = entity_id
                self.__is_loaded['entity_id'] = True

            self.__is_loaded['identity'] = identity
            self.__identity = identity

        return is_authentic

    def get_transactions(self, reload=False):
        """Fetches and returns the iterator to transactions (list of dictionary) for the given entity

        arguments:
        reload (optional) (default: False) -- do not use cached data and refetch from API
        """
        if not self.__is_loaded['entity_id']:
            raise ValueError("no statement uploaded yet so use upload_statement method to set the entity_id")

        if reload or not self.__is_loaded['transactions']:
            timer_start = time.time()
            while time.time() < timer_start + finbox_bankconnect.poll_timeout: # keep polling till timeout happens
                status, accounts, fraud_info, transactions = connector.get_transactions(self.__entity_id)
                if status == "failed":
                    raise ExtractionFailedError
                elif status == "not_found":
                    raise EntityNotFoundError
                elif status == "completed":
                    # save accounts
                    self.__accounts = accounts
                    self.__is_loaded['accounts'] = True
                    # save fraud info
                    self.__fraud_info = fraud_info
                    self.__is_loaded['fraud_info'] = True
                    # save transaction info
                    self.__transactions = transactions
                    self.__is_loaded['transactions'] = True
                    break
                time.sleep(finbox_bankconnect.poll_interval) # delay of finbox_bankconnect.poll_interval

            if not self.__is_loaded['transactions']:
                # if even after polling couldn't get transactions
                raise ServiceTimeOutError

        return iter(self.__transactions)

    def get_identity(self, reload=False):
        """Fetches and returns the identity dictionary (one) for the given entity

        arguments:
        reload (optional) (default: False) -- do not use cached data and refetch from API
        account_id (optional) -- get identity dictionary for specific account_id
        """
        if not self.__is_loaded['entity_id']:
            raise ValueError("no statement uploaded yet so use upload_statement method to set the entity_id")

        if reload or not self.__is_loaded['identity']:
            timer_start = time.time()
            while time.time() < timer_start + finbox_bankconnect.poll_timeout: # keep polling till timeout happens
                status, accounts, fraud_info, identity = connector.get_identity(self.__entity_id)
                if status == "failed":
                    raise ExtractionFailedError
                elif status == "not_found":
                    raise EntityNotFoundError
                elif status == "completed":
                    # save accounts
                    self.__accounts = accounts
                    self.__is_loaded['accounts'] = True
                    # save fraud info
                    self.__fraud_info = fraud_info
                    self.__is_loaded['fraud_info'] = True
                    # save identity info
                    self.__identity = identity
                    self.__is_loaded['identity'] = True
                    break
                time.sleep(finbox_bankconnect.poll_interval) # delay of finbox_bankconnect.poll_interval

            if not self.__is_loaded['identity']:
                # if even after polling couldn't get identity
                raise ServiceTimeOutError

        return self.__identity

    def get_accounts(self, reload=False):
        """Fetches and returns the iterator to accounts (list of dictionary) for the given entity

        arguments:
        reload (optional) (default: False) -- do not use cached data and refetch from API
        """
        if not self.__is_loaded['entity_id']:
            raise ValueError("no statement uploaded yet so use upload_statement method to set the entity_id")

        if reload or not self.__is_loaded['accounts']:
            timer_start = time.time()
            while time.time() < timer_start + finbox_bankconnect.poll_timeout: # keep polling till timeout happens
                status, accounts, fraud_info = connector.get_accounts(self.__entity_id)
                if status == "failed":
                    raise ExtractionFailedError
                elif status == "not_found":
                    raise EntityNotFoundError
                elif status == "completed":
                    # save accounts
                    self.__accounts = accounts
                    self.__is_loaded['accounts'] = True
                    # save fraud info
                    self.__fraud_info = fraud_info
                    self.__is_loaded['fraud_info'] = True
                    break
                time.sleep(finbox_bankconnect.poll_interval) # delay of finbox_bankconnect.poll_interval

            if not self.__is_loaded['accounts']:
                # if even after polling couldn't get accounts
                raise ServiceTimeOutError

        return iter(self.__accounts)

    def get_fraud_info(self, reload=False):
        """Fetches and returns the iterator to fraud info (list of dictionary) for the given entity

        arguments:
        reload (optional) (default: False) -- do not use cached data and refetch from API
        """
        if not self.__is_loaded['entity_id']:
            raise ValueError("no statement uploaded yet so use upload_statement method to set the entity_id")

        if reload or not self.__is_loaded['fraud_info']:
            timer_start = time.time()
            while time.time() < timer_start + finbox_bankconnect.poll_timeout: # keep polling till timeout happens
                status, accounts, fraud_info = connector.get_accounts(self.__entity_id)
                if status == "failed":
                    raise ExtractionFailedError
                elif status == "not_found":
                    raise EntityNotFoundError
                elif status == "completed":
                    # save accounts
                    self.__accounts = accounts
                    self.__is_loaded['accounts'] = True
                    # save fraud info
                    self.__fraud_info = fraud_info
                    self.__is_loaded['fraud_info'] = True
                    break
                time.sleep(finbox_bankconnect.poll_interval) # delay of finbox_bankconnect.poll_interval

            if not self.__is_loaded['fraud_info']:
                # if even after polling couldn't get fraud info
                raise ServiceTimeOutError

        return iter(self.__fraud_info)
