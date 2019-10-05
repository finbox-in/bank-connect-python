name = "finbox_bankconnect"
api_key = None
api_version = 'v1'
max_retry_limit = 2
base_url = 'https://portal.finbox.in'
poll_timeout = 10 # seconds
poll_interval = 2 # seconds

#TODO: Add authentication mode and also secret key + timestamp based authentication mode
from finbox_bankconnect.entity import Entity
