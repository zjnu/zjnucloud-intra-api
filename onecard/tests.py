from django.test import TestCase

# Create your tests here.
from onecard import core


class OneCardTestCase(TestCase):

    def setUp(self):
        self.transaction = core.OneCardTransactions('13211137', '030932')

    def test_daily_transaction(self):
        pass
        # print(self.transaction.get_daily())

    def test_monthly_transaction(self):
        print(self.transaction.get_monthly(2016, 6))
