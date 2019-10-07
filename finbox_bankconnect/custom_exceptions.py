class ExtractionFailedError(Exception):
    def __init__(self):
        Exception.__init__(self, "Couldn't extract transactions from the given statement")

class EntityNotFoundError(Exception):
    def __init__(self):
        Exception.__init__(self, "Couldn't find the entity with given entity_id")

class ServiceTimeOutError(Exception):
    def __init__(self):
        Exception.__init__(self, "Couldn't reach the service")

class InvalidBankNameError(Exception):
    def __init__(self):
        Exception.__init__(self, "Please enter a valid bank name string")

class PasswordIncorrectError(Exception):
    def __init__(self):
        Exception.__init__(self, "Incorrect password for the pdf file")

class UnparsablePDFError(Exception):
    def __init__(self):
        Exception.__init__(self, "Given PDF either has only image or is not in a format that can be parsed")

class FileProcessFailedError(Exception):
    def __init__(self):
        Exception.__init__(self, "Could not process document. If you think it was an error, contact Finbox.")

class CannotIdentityBankError(Exception):
    def __init__(self):
        Exception.__init__(self, "Cannot identify the bank from the document, try specifying the bank_name explicitly")
