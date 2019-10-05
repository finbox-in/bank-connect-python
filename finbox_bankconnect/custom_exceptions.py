class ExtractionFailedError(Exception):
    def __init__(self):
        Exception.__init__(self, "Couldn't extract transactions from the given statement")

class EntityNotFoundError(Exception):
    def __init__(self):
        Exception.__init__(self, "Couldn't find the entity with given entity_id")

class ServiceTimeOutError(Exception):
    def __init__(self):
        Exception.__init__(self, "Couldn't reach the service")
