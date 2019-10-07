import unittest
import os
import finbox_bankconnect as bc

class TestTransactions(unittest.TestCase):

    def setUp(self):
        bc.api_key = os.environ['TEST_API_KEY']
        entity = bc.Entity.get(entity_id=os.environ['TEST_ENTITY_ID'])
        self.first_transaction = next(entity.get_transactions())

    def test_balance_exists(self):
        self.assertIn("balance", self.first_transaction)

    def test_transaction_type_exists(self):
        self.assertIn("transaction_type", self.first_transaction)

    def test_date_exists(self):
        self.assertIn("date", self.first_transaction)

if __name__ == '__main__':
    unittest.main()
