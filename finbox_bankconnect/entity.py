from collections import defaultdict
import time
import datetime
from finbox_bankconnect.utils import is_valid_uuid4
from finbox_bankconnect.filters import make_account_id_filter, make_daterange_filter
import finbox_bankconnect.connector as connector
from finbox_bankconnect.custom_exceptions import ExtractionFailedError, EntityNotFoundError, ServiceTimeOutError
import finbox_bankconnect

class Entity:
    def __init__(self, source=None, entity_id=None, link_id=None):
        if source is None or not type(source) == str:
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
        self.__lender_transactions = []

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
        if not type(entity_id) == str:
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
        if link_id and not type(link_id) == str:
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
        if not type(file_path) == str:
            raise ValueError("file_path must be a string")
        if not file_path.lower().endswith('.pdf'):
            raise ValueError("file_path must be of a pdf file")

        if pdf_password is not None and not type(pdf_password) == str:
            raise ValueError("pdf_password must be a string or None")

        if bank_name and not type(bank_name) == str:
            raise ValueError("bank_name must be a string or None")
        if bank_name == "":
            bank_name = None

        with open(file_path, 'rb') as file_obj: #throws IOError if file is unaccessible or doesn't exists

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

    def get_transactions(self, reload=False, account_id=None, from_date=None, to_date=None):
        """Fetches and returns the iterator to transactions (list of dictionary) for the given entity

        arguments:
        reload (optional) (default: False) -- do not use cached data and refetch from API
        account_id (optional) -- get transactions for specific account_id
        from_date (optional) -- get transactions greater than or equal to from_date (must be datetime.date)
        to_date (optional) -- get transactions less than or equal to to_date (must be datetime.date)
        """
        if not self.__is_loaded['entity_id']:
            raise ValueError("no statement uploaded yet so use upload_statement method to set the entity_id")

        if account_id is not None:
            if not is_valid_uuid4(account_id):
                raise ValueError("account_id if provided must be a valid UUID4 string")

        if from_date is not None:
            if not type(from_date) == datetime.date:
                raise ValueError("from_date if provided must be a python datetime.date object")
        if to_date is not None:
            if not type(to_date) == datetime.date:
                raise ValueError("to_date if provided must be a python datetime.date object")

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

        if account_id is not None:
            account_id_filter = make_account_id_filter(account_id)
            return filter(account_id_filter, self.__transactions)

        if from_date is not None or to_date is not None:
            daterange_filter = make_daterange_filter(from_date, to_date)
            return filter(daterange_filter, self.__transactions)

        return iter(self.__transactions)

    def get_identity(self, reload=False):
        """Fetches and returns the identity dictionary (one) for the given entity

        arguments:
        reload (optional) (default: False) -- do not use cached data and refetch from API
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

    def __fetch_recurring(self):

        # internal function to update the credit and debit recurring

        if not self.__is_loaded['entity_id']:
            raise ValueError("no statement uploaded yet so use upload_statement method to set the entity_id")

        timer_start = time.time()
        while time.time() < timer_start + finbox_bankconnect.poll_timeout: # keep polling till timeout happens
            status, accounts, fraud_info, credit_recurring, debit_recurring = connector.get_recurring(self.__entity_id)
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
                # save info
                self.__credit_recurring = credit_recurring
                self.__is_loaded['credit_recurring'] = True
                self.__debit_recurring = debit_recurring
                self.__is_loaded['debit_recurring'] = True
                break
            time.sleep(finbox_bankconnect.poll_interval) # delay of finbox_bankconnect.poll_interval

        if not self.__is_loaded['credit_recurring']:
            # if even after polling couldn't get
            raise ServiceTimeOutError

    def get_credit_recurring(self, reload=False, account_id=None):
        """Fetches and returns the iterator to credit recurring transactions (list of dictionary) for the given entity

        arguments:
        reload (optional) (default: False) -- do not use cached data and refetch from API
        account_id (optional) -- get credit recurring transactions for specific account_id
        """
        if account_id is not None:
            if not is_valid_uuid4(account_id):
                raise ValueError("account_id if provided must be a valid UUID4 string")

        if reload or not self.__is_loaded['credit_recurring']:
            self.__fetch_recurring()

        if account_id is not None:
            account_id_filter = make_account_id_filter(account_id)
            return filter(account_id_filter, self.__credit_recurring)

        return iter(self.__credit_recurring)

    def get_debit_recurring(self, reload=False, account_id=None):
        """Fetches and returns the iterator to debit recurring transactions (list of dictionary) for the given entity

        arguments:
        reload (optional) (default: False) -- do not use cached data and refetch from API
        account_id (optional) -- get debit recurring transactions for specific account_id
        """
        if account_id is not None:
            if not is_valid_uuid4(account_id):
                raise ValueError("account_id if provided must be a valid UUID4 string")

        if reload or not self.__is_loaded['debit_recurring']:
            self.__fetch_recurring()

        if account_id is not None:
            account_id_filter = make_account_id_filter(account_id)
            return filter(account_id_filter, self.__debit_recurring)

        return iter(self.__debit_recurring)

    def get_salary(self, reload=False, account_id=None, from_date=None, to_date=None):
        """Fetches and returns the iterator to salary transactions (list of dictionary) for the given entity

        arguments:
        reload (optional) (default: False) -- do not use cached data and refetch from API
        account_id (optional) -- get salary transactions for specific account_id
        from_date (optional) -- get salary transactions greater than or equal to from_date (must be datetime.date)
        to_date (optional) -- get salary transactions less than or equal to to_date (must be datetime.date)
        """
        if not self.__is_loaded['entity_id']:
            raise ValueError("no statement uploaded yet so use upload_statement method to set the entity_id")

        if account_id is not None:
            if not is_valid_uuid4(account_id):
                raise ValueError("account_id if provided must be a valid UUID4 string")

        if from_date is not None:
            if not type(from_date) == datetime.date:
                raise ValueError("from_date if provided must be a python datetime.date object")
        if to_date is not None:
            if not type(to_date) == datetime.date:
                raise ValueError("to_date if provided must be a python datetime.date object")

        if reload or not self.__is_loaded['salary']:
            timer_start = time.time()
            while time.time() < timer_start + finbox_bankconnect.poll_timeout: # keep polling till timeout happens
                status, accounts, fraud_info, salary = connector.get_salary(self.__entity_id)
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
                    # save info
                    self.__salary = salary
                    self.__is_loaded['salary'] = True
                    break
                time.sleep(finbox_bankconnect.poll_interval) # delay of finbox_bankconnect.poll_interval

            if not self.__is_loaded['salary']:
                # if even after polling couldn't get
                raise ServiceTimeOutError

        if account_id is not None:
            account_id_filter = make_account_id_filter(account_id)
            return filter(account_id_filter, self.__salary)

        if from_date is not None or to_date is not None:
            daterange_filter = make_daterange_filter(from_date, to_date)
            return filter(daterange_filter, self.__salary)

        return iter(self.__salary)

    def get_lender_transactions(self, reload=False, account_id=None, from_date=None, to_date=None):
        """Fetches and returns the iterator to lender transactions (list of dictionary) for the given entity

        arguments:
        reload (optional) (default: False) -- do not use cached data and refetch from API
        account_id (optional) -- get lender transactions for specific account_id
        from_date (optional) -- get lender transactions greater than or equal to from_date (must be datetime.date)
        to_date (optional) -- get lender transactions less than or equal to to_date (must be datetime.date)
        """
        if not self.__is_loaded['entity_id']:
            raise ValueError("no statement uploaded yet so use upload_statement method to set the entity_id")

        if account_id is not None:
            if not is_valid_uuid4(account_id):
                raise ValueError("account_id if provided must be a valid UUID4 string")

        if from_date is not None:
            if not type(from_date) == datetime.date:
                raise ValueError("from_date if provided must be a python datetime.date object")
        if to_date is not None:
            if not type(to_date) == datetime.date:
                raise ValueError("to_date if provided must be a python datetime.date object")

        if reload or not self.__is_loaded['lender_transactions']:
            timer_start = time.time()
            while time.time() < timer_start + finbox_bankconnect.poll_timeout: # keep polling till timeout happens
                status, accounts, fraud_info, lender_transactions = connector.get_lender_transactions(self.__entity_id)
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
                    # save info
                    self.__lender_transactions = lender_transactions
                    self.__is_loaded['lender_transactions'] = True
                    break
                time.sleep(finbox_bankconnect.poll_interval) # delay of finbox_bankconnect.poll_interval

            if not self.__is_loaded['lender_transactions']:
                # if even after polling couldn't get
                raise ServiceTimeOutError

        if account_id is not None:
            account_id_filter = make_account_id_filter(account_id)
            return filter(account_id_filter, self.__lender_transactions)

        if from_date is not None or to_date is not None:
            daterange_filter = make_daterange_filter(from_date, to_date)
            return filter(daterange_filter, self.__lender_transactions)

        return iter(self.__lender_transactions)
