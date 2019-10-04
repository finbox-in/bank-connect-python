from utils import is_valid_uuid4, check_progress
from collections import defaultdict
import time
from custom_exceptions import *

class Entity:
    def __init__(self, source=None, entity_id=None, link_id=None):
        if source is None or not isinstance(source, int):
            raise ValueError("must create entity using get or create methods of Entity class")

        # basic identifiers
        self.__entity_id = entity_id
        self.__link_id = link_id

        # lists to keep track of different transactions
        self.__transactions = []
        self.__credit_recurring = []
        self.__debit_recurring = []
        self.__salary = []

        # lazy loading trackers and polling lock
        self.__is_loaded = defaultdict(bool)
        self.__poll_lock = False

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

    def upload_statement(self, file_path, bank_name=None):
        """Uploads the statement for the given entity instance, creates entity if required too

        arguments:
        file_path -- path of the pdf file
        bank_name (optional) -- bank name string
        """
        if not file_path:
            raise ValueError("file_path cannot be blank or None")
        if not isinstance(file_path, str):
            raise ValueError("file_path must be a string")
        if not file_path.lower().endswith('.pdf'):
            raise ValueError("file_path must be of a pdf file")

        if bank_name and not isinstance(bank_name, str):
            raise ValueError("bank_name must be a string or None")
        if bank_name == "":
            bank_name = None

        with open(file_path) as file_obj: #throws IOError if file is unaccessible or doesn't exists

            if self.__is_loaded['link_id'] and not self.__is_loaded['entity_id']:
                # create an entity with the link_id and set it
                self.__entity_id = connector.create_entity(self.__link_id)
                self.__is_loaded['entity_id'] = True

            success, response = connector.upload_file(self.__entity_id, file_obj, bank_name)

            if success:
                if not self.__is_loaded['entity_id']:
                    self.__entity_id = response['entity_id']
                    self.__is_loaded['entity_id'] = True

    def get_transactions(self, reload=False):
        if not self.__is_loaded['entity_id']:
            raise ValueError("no statement uploaded yet so use upload_statement method to set the entity_id")

        if reload or not self.__is_loaded['transactions']:
            if not self.__poll_lock: # lock is free
                self.__poll_lock = True # acquire lock

                timer_start = time.time()
                while time.time() < timer_start + poll_timeout: # keep polling till timeout happens
                    time.sleep(poll_interval) # delay of poll_interval
                    response = connector.get_transactions(self.__entity_id)
                    status = check_progress(response.get('progress', None))
                    if status == "failed":
                        self.__poll_lock = False
                        raise ExtractionFailedError
                    elif status == "not_found":
                        self.__poll_lock = False
                        raise EntityNotFoundError
                    elif status == "completed":
                        # save accounts, fraud and transaction info

                self.__poll_lock = False # release lock


        return self.transactions
