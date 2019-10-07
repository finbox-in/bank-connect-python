import unittest
import os
import finbox_bankconnect as bc
from finbox_bankconnect.custom_exceptions import EntityNotFoundError

class TestGetEntityEdgeCases(unittest.TestCase):

    def setUp(self):
        bc.api_key = os.environ['TEST_API_KEY']

    def test_empty_entity_id(self):
        exception_handled = False
        try:
            bc.Entity.get(entity_id = '')
            bc.Entity.get(entity_id = None)
        except ValueError:
            exception_handled = True
        self.assertEqual(exception_handled, True, "entity_id None and blank string case - not handled")

    def test_invalid_entity_id(self):
        exception_handled = False
        try:
            bc.Entity.get(entity_id = '123123123safasd')
            bc.Entity.get(entity_id = 'c036e96dccae443c8f64b98ceeaa1578')
        except ValueError:
            exception_handled = True
        self.assertEqual(exception_handled, True, "entity_id not a valid uuid4 (with hyphen) case - not handled")

    def test_detail_not_found(self):
        exception_handled = False
        try:
            entity = bc.Entity.get(entity_id = 'c036e96d-ccae-443c-8f64-b98ceeaa1578')
            entity.get_transactions()
            # assuming this uuid id doesn't exists in DB :P
        except EntityNotFoundError:
            exception_handled = True
        self.assertEqual(exception_handled, True, "entity_id valid but not in DB case - not handled")


class TestFetchTransactions(unittest.TestCase):

    def setUp(self):
        bc.api_key = os.environ['TEST_API_KEY']
        entity = bc.Entity.get(entity_id=os.environ['TEST_ENTITY_ID'])
        self.first_transaction = next(entity.get_transactions())

    def test_balance_exists(self):
        self.assertIn("balance", self.first_transaction, "balance not present in transaction")

    def test_transaction_type_exists(self):
        self.assertIn("transaction_type", self.first_transaction, "balance not present in transaction")

    def test_date_exists(self):
        self.assertIn("date", self.first_transaction, "balance not present in transaction")

if __name__ == '__main__':
    unittest.main()
