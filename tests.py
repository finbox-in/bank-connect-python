"""
To run the test cases below make sure you have following environment variables set:

TEST_API_KEY -- API Key for your organization
TEST_LINK_ID -- any link_id string
TEST_ENTITY_ID -- any entity id which you have created before using any of our APIs / libraries before under the above organization
                  with link_id as above (TEST_LINK_ID)
TEST_ACCOUNT_ID -- an account id of the above TEST_ENTITY_ID entity having some transactions

Make sure the statement used for testing has at least one salary, lender, credit, debit transaction under the above account id

"""

import unittest
import os
import datetime
import finbox_bankconnect as fbc
from finbox_bankconnect.custom_exceptions import EntityNotFoundError, PasswordIncorrectError
from finbox_bankconnect.custom_exceptions import UnparsablePDFError, CannotIdentityBankError
from finbox_bankconnect.utils import is_valid_uuid4

NOT_EXISTS_ENTITY_ID = "c036e96d-ccae-443c-8f64-b98ceeaa1578"

class TestUtilFunctions(unittest.TestCase):
    """
    Test cases for utility functions
    """

    def test_valid_uuid4(self):
        self.assertEqual(is_valid_uuid4("c036e96d-ccae-443c-8f64-b98ceeaa1578"), True, "valid uuid4 detected as invalid")

    def test_uuid4_without_hyphen(self):
        self.assertEqual(is_valid_uuid4("c036e96dccae443c8f64b98ceeaa1578"), False, "valid uuid4 without hyphen must be invalid")

    def test_string_not_uuid4(self):
        self.assertEqual(is_valid_uuid4("abc"), False, "invalid uuid4 string detected as valid")

    def test_integer(self):
        self.assertEqual(is_valid_uuid4(123), False, "integer detected as valid uui4")

    def test_list(self):
        self.assertEqual(is_valid_uuid4(["sadasd", "asdasd"]), False, "list detected as valid uui4")

    def test_none(self):
        self.assertEqual(is_valid_uuid4(None), False, "list detected as valid uui4")

class TestGetEntityEdgeCases(unittest.TestCase):
    """
    Test edge cases for Entity.get function
    """

    def setUp(self):
        fbc.api_key = os.environ['TEST_API_KEY']

    def test_empty_entity_id(self):
        exception_handled = False
        try:
            fbc.Entity.get(entity_id = '')
        except ValueError:
            exception_handled = True
        except Exception as e:
            print(e)
        self.assertEqual(exception_handled, True, "entity_id blank string case - not handled")

    def test_none_entity_id(self):
        exception_handled = False
        try:
            fbc.Entity.get(entity_id = None)
        except ValueError:
            exception_handled = True
        except Exception as e:
            print(e)
        self.assertEqual(exception_handled, True, "entity_id none case - not handled")

    def test_invalid_entity_id(self):
        exception_handled = False
        try:
            fbc.Entity.get(entity_id = 'c036e96dccae443c8f64b98ceeaa1578')
        except ValueError:
            exception_handled = True
        except Exception as e:
            print(e)
        self.assertEqual(exception_handled, True, "entity_id not a valid uuid4 (with hyphen) case - not handled")

    def test_non_string_entity_id(self):
        list_handled = False
        int_handled = False
        try:
            fbc.Entity.get(entity_id = ["hello"])
        except ValueError:
            list_handled = True
        except Exception as e:
            print(e)
        try:
            fbc.Entity.get(entity_id = 123)
        except ValueError:
            int_handled = True
        except Exception as e:
            print(e)
        self.assertEqual(list_handled and int_handled, True, "entity_id non string case - not handled")

    def test_detail_not_found_identity(self):
        exception_handled = False
        try:
            entity = fbc.Entity.get(entity_id = NOT_EXISTS_ENTITY_ID)
            entity.get_identity()
        except EntityNotFoundError:
            exception_handled = True
        except Exception as e:
            print(e)
        self.assertEqual(exception_handled, True, "entity_id valid but not in DB case, not handled in get_identity")

    def test_detail_not_found_transactions(self):
        exception_handled = False
        try:
            entity = fbc.Entity.get(entity_id = NOT_EXISTS_ENTITY_ID)
            entity.get_transactions()
        except EntityNotFoundError:
            exception_handled = True
        except Exception as e:
            print(e)
        self.assertEqual(exception_handled, True, "entity_id valid but not in DB case, not handled in get_transactions")

    def test_detail_not_found_fraud_info(self):
        exception_handled = False
        try:
            entity = fbc.Entity.get(entity_id = NOT_EXISTS_ENTITY_ID)
            entity.get_fraud_info()
        except EntityNotFoundError:
            exception_handled = True
        except Exception as e:
            print(e)
        self.assertEqual(exception_handled, True, "entity_id valid but not in DB case, not handled in get_fraud_info")

    def test_detail_not_found_accounts(self):
        exception_handled = False
        try:
            entity = fbc.Entity.get(entity_id = NOT_EXISTS_ENTITY_ID)
            entity.get_accounts()
        except EntityNotFoundError:
            exception_handled = True
        except Exception as e:
            print(e)
        self.assertEqual(exception_handled, True, "entity_id valid but not in DB case, not handled in get_accounts")

class TestLinkIdFlow(unittest.TestCase):
    """
    Test the flow by using the link_id
    """

    def setUp(self):
        fbc.api_key = os.environ['TEST_API_KEY']

    def test_non_string_link_id(self):
        list_handled = False
        int_handled = False
        try:
            fbc.Entity.create(link_id = ["hello"])
        except ValueError:
            list_handled = True
        except Exception as e:
            print(e)
        try:
            fbc.Entity.create(link_id = 123)
        except ValueError:
            int_handled = True
        except Exception as e:
            print(e)
        self.assertEqual(list_handled and int_handled, True, "link_id non string case - not handled")

    def test_entity_creation(self):
        entity = fbc.Entity.create(link_id = "python_link_id_test_1")
        entity_id = entity.entity_id
        self.assertEqual(is_valid_uuid4(entity_id), True, "entity_id couldn't be created against the link_id")

    def test_link_id_fetch(self):
        entity = fbc.Entity.get(entity_id=os.environ['TEST_ENTITY_ID'])
        self.assertEqual(entity.link_id, os.environ['TEST_LINK_ID'], "link_id was incorrectly fetched")

class TestIdentity(unittest.TestCase):
    """
    Test identity when using get_accounts function
    """
    def setUp(self):
        fbc.api_key = os.environ['TEST_API_KEY']
        entity = fbc.Entity.get(entity_id=os.environ['TEST_ENTITY_ID'])
        self.identity = entity.get_identity()

    def test_name(self):
        self.assertIn("name", self.identity, "name not present in identity")

    def test_account_id(self):
        self.assertIn("account_id", self.identity, "account_id not present in identity")

    def test_account_number(self):
        self.assertIn("account_number", self.identity, "account_number not present in identity")

    def test_address(self):
        self.assertIn("address", self.identity, "address not present in identity")

class TestAccounts(unittest.TestCase):
    """
    Test accounts when using get_accounts function
    """
    def setUp(self):
        fbc.api_key = os.environ['TEST_API_KEY']
        entity = fbc.Entity.get(entity_id=os.environ['TEST_ENTITY_ID'])
        self.first_account = next(entity.get_accounts())

    def test_months(self):
        self.assertIn("months", self.first_account, "months not present in account")

    def test_account_id(self):
        self.assertIn("account_id", self.first_account, "account_id not present in account")

    def test_account_number(self):
        self.assertIn("account_number", self.first_account, "account_number not present in account")

class TestFraudInfo(unittest.TestCase):
    """
    Test fraud info when using get_accounts function
    """
    def setUp(self):
        fbc.api_key = os.environ['TEST_API_KEY']
        entity = fbc.Entity.get(entity_id=os.environ['TEST_ENTITY_ID'])
        self.first_fraud = next(entity.get_fraud_info())

    def test_fraud_type(self):
        self.assertIn("fraud_type", self.first_fraud, "months not present in fraud")

    def test_statement_id(self):
        self.assertIn("statement_id", self.first_fraud, "statement_id not present in fraud")

class TestFetchTransactions(unittest.TestCase):
    """
    Test transaction response when using get_transactions function
    """

    def setUp(self):
        fbc.api_key = os.environ['TEST_API_KEY']
        entity = fbc.Entity.get(entity_id=os.environ['TEST_ENTITY_ID'])
        self.first_transaction = next(entity.get_transactions())

    def test_balance_exists(self):
        self.assertIn("balance", self.first_transaction, "balance not present in transaction")

    def test_transaction_type_exists(self):
        self.assertIn("transaction_type", self.first_transaction, "balance not present in transaction")

    def test_date_exists(self):
        self.assertIn("date", self.first_transaction, "balance not present in transaction")

class TestFetchRecurring(unittest.TestCase):
    """
    Test response when using get_credit_recurring and get_debit_recurring function
    """

    def setUp(self):
        fbc.api_key = os.environ['TEST_API_KEY']
        entity = fbc.Entity.get(entity_id=os.environ['TEST_ENTITY_ID'])
        self.first_r_credit = next(entity.get_credit_recurring())
        self.first_r_debit = next(entity.get_debit_recurring())

    def test_credit_account_id_exists(self):
        self.assertIn("account_id", self.first_r_credit, "account_id not present in credit recurring")

    def test_credit_transactions(self):
        self.assertIn("transactions", self.first_r_credit, "transactions not present in credit recurring")

    def test_debit_account_id_exists(self):
        self.assertIn("account_id", self.first_r_debit, "account_id not present in debit recurring")

    def test_debit_transactions(self):
        self.assertIn("transactions", self.first_r_debit, "transactions not present in debit recurring")

class TestFetchSalary(unittest.TestCase):
    """
    Test response when using get_salary function
    """

    def setUp(self):
        fbc.api_key = os.environ['TEST_API_KEY']
        entity = fbc.Entity.get(entity_id=os.environ['TEST_ENTITY_ID'])
        self.first_salary = next(entity.get_salary())

    def test_balance_exists(self):
        self.assertIn("balance", self.first_salary, "balance not present in salary")

    def test_transaction_type_exists(self):
        self.assertIn("transaction_type", self.first_salary, "balance not present in salary")

    def test_date_exists(self):
        self.assertIn("date", self.first_salary, "balance not present in salary")

class TestFetchLenderTransactions(unittest.TestCase):
    """
    Test response when using get_lender_transactions function
    """

    def setUp(self):
        fbc.api_key = os.environ['TEST_API_KEY']
        entity = fbc.Entity.get(entity_id=os.environ['TEST_ENTITY_ID'])
        self.first_lender_txn = next(entity.get_lender_transactions())

    def test_balance_exists(self):
        self.assertIn("balance", self.first_lender_txn, "balance not present in lender transaction")

    def test_transaction_type_exists(self):
        self.assertIn("transaction_type", self.first_lender_txn, "balance not present in lender transaction")

    def test_date_exists(self):
        self.assertIn("date", self.first_lender_txn, "balance not present in lender transaction")

class TestAccountEdgeCases(unittest.TestCase):
    """
    Test edge cases for invalid account_id
    """

    def setUp(self):
        fbc.api_key = os.environ['TEST_API_KEY']
        self.entity = fbc.Entity.get(entity_id=os.environ['TEST_ENTITY_ID'])

    def test_invalid_account_id(self):
        array_handled = False
        invalid_uuid4_handled = False
        try:
            next(self.entity.get_transactions(account_id=['hello']))
        except ValueError:
            array_handled = True
        try:
            next(self.entity.get_transactions(account_id="somelongstringispresenthere"))
        except ValueError:
            invalid_uuid4_handled = True
        self.assertEqual(array_handled and invalid_uuid4_handled, True,
            "array and invalid uuid4 string cases not handled for get_transactions with account_id")

class TestAccountFilteredTransactions(unittest.TestCase):
    """
    Test transaction response when using get_transactions function with account_id filter
    """

    def setUp(self):
        fbc.api_key = os.environ['TEST_API_KEY']
        entity = fbc.Entity.get(entity_id=os.environ['TEST_ENTITY_ID'])
        self.first_transaction = next(entity.get_transactions(account_id = os.environ['TEST_ACCOUNT_ID']))

    def test_balance_exists(self):
        self.assertIn("balance", self.first_transaction, "balance not present in transaction")

    def test_transaction_type_exists(self):
        self.assertIn("transaction_type", self.first_transaction, "balance not present in transaction")

    def test_date_exists(self):
        self.assertIn("date", self.first_transaction, "balance not present in transaction")

class TestDateRangeEdgeCases(unittest.TestCase):
    """
    Test edge cases for invalid date ranges
    """

    def setUp(self):
        fbc.api_key = os.environ['TEST_API_KEY']
        self.entity = fbc.Entity.get(entity_id=os.environ['TEST_ENTITY_ID'])

    def test_invalid_daterange(self):
        string_handled = False
        try:
            next(self.entity.get_transactions(from_date="2019-10-04 00:00:00", to_date="2019-10-31 00:00:00"))
        except ValueError:
            string_handled = True
        datetime_handled = False
        try:
            next(self.entity.get_transactions(from_date=datetime.datetime.today(), to_date=datetime.datetime.now()))
        except ValueError:
            datetime_handled = True
        self.assertEqual(string_handled and datetime_handled, True,
            "datetime with/without tzinfo cases not handled for get_transactions with from_date and to_date")

class TestDateRangeFilteredTransactions(unittest.TestCase):
    """
    Test transaction response when using get_transactions function with from_date and to_date filter
    """

    def setUp(self):
        fbc.api_key = os.environ['TEST_API_KEY']
        entity = fbc.Entity.get(entity_id=os.environ['TEST_ENTITY_ID'])
        from_date = (datetime.datetime.today() - datetime.timedelta(days=1000)).date()
        self.first_transaction = next(entity.get_transactions(from_date=from_date, to_date=datetime.datetime.today().date()))

    def test_balance_exists(self):
        self.assertIn("balance", self.first_transaction, "balance not present in transaction")

    def test_transaction_type_exists(self):
        self.assertIn("transaction_type", self.first_transaction, "balance not present in transaction")

    def test_date_exists(self):
        self.assertIn("date", self.first_transaction, "balance not present in transaction")

class TestUploadStatement(unittest.TestCase):
    """
    Test uploading of statement pdf with edge cases
    """

    def setUp(self):
        fbc.api_key = os.environ['TEST_API_KEY']

    def test_empty_file_path(self):
        none_handled = False
        blank_handled = False
        entity = fbc.Entity.create()
        try:
            entity.upload_statement(None, bank_name='axis')
        except ValueError:
            none_handled = True
        except Exception as e:
            print(e)
        try:
            entity.upload_statement('', bank_name='axis')
        except ValueError:
            blank_handled = True
        except Exception as e:
            print(e)
        self.assertEqual(none_handled and blank_handled, True, "None and/or blank string file path not handled for upload")

    def test_non_string_file_path(self):
        exception_handled = False
        entity = fbc.Entity.create()
        try:
            entity.upload_statement(['hello.pdf'], bank_name='axis')
        except ValueError:
            exception_handled = True
        except Exception as e:
            print(e)
        self.assertEqual(exception_handled, True, "Non string file path error not handled")

    def test_non_pdf_file_path(self):
        exception_handled = False
        entity = fbc.Entity.create()
        try:
            entity.upload_statement('README.md', bank_name='axis')
        except ValueError:
            exception_handled = True
        except Exception as e:
            print(e)
        self.assertEqual(exception_handled, True, "Non pdf path error not handled")

    def test_password_incorrect_bank_name(self):
        exception_handled = False
        entity = fbc.Entity.create()
        try:
            entity.upload_statement('samples/test_statement_2.pdf', pdf_password='wrongpass', bank_name='axis')
        except PasswordIncorrectError:
            exception_handled = True
        except Exception as e:
            print(e)
        self.assertEqual(exception_handled, True, "Password incorrect error not handled")

    def test_unparsable_pdf_bank_name(self):
        exception_handled = False
        entity = fbc.Entity.create()
        try:
            entity.upload_statement('samples/test_statement_2.pdf', pdf_password='finbox', bank_name='axis')
        except UnparsablePDFError:
            exception_handled = True
        except Exception as e:
            print(e)
        self.assertEqual(exception_handled, True, "Unparsable PDF error not handled")

    def test_cannot_identify_bank(self):
        exception_handled = False
        entity = fbc.Entity.create()
        try:
            entity.upload_statement('samples/test_statement_2.pdf', pdf_password='finbox')
        except CannotIdentityBankError:
            exception_handled = True
        except Exception as e:
            print(e)
        self.assertEqual(exception_handled, True, "Cannot identify bank error not handled")

    def test_success_upload_file_bank_name(self):
        entity = fbc.Entity.create()
        is_authentic = entity.upload_statement('samples/test_statement_1.pdf', pdf_password='finbox', bank_name='axis')
        self.assertEqual(is_authentic, False, "Statement file upload and fraud check failed")

    def test_success_upload_file(self):
        entity = fbc.Entity.create()
        is_authentic = entity.upload_statement('samples/test_statement_1.pdf', pdf_password='finbox')
        self.assertEqual(is_authentic, False, "Bankless Statement file upload and fraud check failed")

    def test_success_upload_file_link_id(self):
        entity = fbc.Entity.create(link_id='python_link_id_test_2')
        is_authentic = entity.upload_statement('samples/test_statement_1.pdf', pdf_password='finbox', bank_name='axis')
        self.assertEqual(is_authentic, False, "Statement file upload against link id and fraud check failed")

if __name__ == '__main__':
    unittest.main()
