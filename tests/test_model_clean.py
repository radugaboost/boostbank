from django.test import TestCase
from bank_app import models, scripts
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import date


class TransactCleanTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            is_superuser=True,
            username='test',
            first_name='test',
            last_name='test',
            email='test@mail.ru',
            password='test'
        )
        self.client = models.Client.objects.create(
            user=self.user,
            phone_number='89185467890'
        )
        tariff_1 = models.TariffAccount.objects.get(
            type='Deposit'
        )
        tariff_2 = models.TariffAccount.objects.get(
            type='Saving'
        )
        self.account_1 = models.Account.objects.create(
            client=self.client,
            tariff=tariff_1,
            funds=10000
        )
        self.account_2 = models.Account.objects.create(
            client=self.client,
            tariff=tariff_2,
            funds=10000
        )

    def test_valid(self):
        init_funds_sender = self.account_1.funds
        transact = models.Transact.objects.create(
            sender=self.account_1,
            recipient=self.account_2,
            amount=100
        )

        self.assertIsNotNone(transact.pk)
        self.assertTrue(init_funds_sender > self.account_1.funds)
        self.assertEqual(transact.sender, self.account_1)
        self.assertEqual(transact.recipient, self.account_2)

    def test_invalid(self):
        with self.assertRaises(ValidationError):
            models.Transact.objects.create(
                sender=self.account_1,
                recipient=self.account_1,
                amount=100
            )

    def test_str(self):
        transact = models.Transact.objects.create(
            sender=self.account_1,
            recipient=self.account_2,
            amount=100
        )
        expected_string = 'From {0} to {1} | {2} | {3}'.format(
            transact.sender.client,
            transact.recipient.client,
            transact.amount,
            transact.created
        )
        self.assertEqual(str(transact), expected_string)


class PaymentCleanTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            is_superuser=True,
            username='test',
            first_name='test',
            last_name='test',
            email='test@mail.ru',
            password='test'
        )
        self.client = models.Client.objects.create(
            user=self.user,
            phone_number='89185467890'
        )
        tariff_1 = models.TariffAccount.objects.get(
            type='Deposit'
        )
        tariff_2 = models.TariffAccount.objects.get(
            type='Saving'
        )
        self.account_1 = models.Account.objects.create(
            client=self.client,
            tariff=tariff_1,
            funds=10000
        )
        self.account_2 = models.Account.objects.create(
            client=self.client,
            tariff=tariff_2,
            funds=10000
        )

    def test_invalid(self):
        with self.assertRaises(ValidationError):
            models.Payment.objects.create(
                sender=self.account_1,
                recipient=self.account_1,
                amount=100
            )

    def test_valid(self):
        payment = models.Payment.objects.create(
            sender=self.account_1,
            recipient=self.account_2,
            amount=100
        )

        self.assertIsNotNone(payment.pk)
        self.assertEqual(payment.sender, self.account_1)
        self.assertEqual(payment.recipient, self.account_2)

    def test_str(self):
        payment = models.Payment.objects.create(
            sender=self.account_1,
            recipient=self.account_2,
            amount=100
        )
        expected_string = 'To {0} | {1} | {2}'.format(
            payment.recipient.client,
            payment.amount,
            payment.status
        )
        self.assertEqual(str(payment), expected_string)


class InvestmenCleanTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            is_superuser=True,
            username='test',
            first_name='test',
            last_name='test',
            email='test@mail.ru',
            password='test'
        )
        self.client = models.Client.objects.create(
            user=self.user,
            phone_number='89185467890'
        )
        tariff_1 = models.TariffAccount.objects.get(
            type='Deposit'
        )
        tariff_2 = models.TariffAccount.objects.get(
            type='Saving'
        )
        self.account_1 = models.Account.objects.create(
            client=self.client,
            tariff=tariff_1,
            funds=10000
        )
        self.account_2 = models.Account.objects.create(
            client=self.client,
            tariff=tariff_2,
            funds=10000
        )
        self.invest_tariff = models.TariffInvestment.objects.get(
            type='Stock'
        )

    def test_invalid(self):
        bank_account = scripts.bank_max_funds()
        bank = bank_account.client
        with self.assertRaises(ValidationError):
            models.Investment.objects.create(
                client=bank,
                recipient_account=bank_account,
                payment_account=bank_account,
                amount=1000,
                term=12,
                tariff=self.invest_tariff
            )

    def test_str(self):
        investment = models.Investment.objects.create(
            client=self.client,
            payment_account=self.account_1,
            recipient_account=self.account_2,
            tariff=self.invest_tariff,
            amount=10000,
            term=10
        )
        expected_string = '{0} | {1} | {2}'.format(
            investment.client,
            investment.tariff.type,
            investment.remaining_amount
        )
        self.assertEqual(str(investment), expected_string)


class CreditCleanTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            is_superuser=True,
            username='test',
            first_name='test',
            last_name='test',
            email='test@mail.ru',
            password='test'
        )
        self.client = models.Client.objects.create(
            user=self.user,
            phone_number='89185467890'
        )
        tariff_1 = models.TariffAccount.objects.get(
            type='Deposit'
        )
        tariff_2 = models.TariffAccount.objects.get(
            type='Saving'
        )
        self.account_1 = models.Account.objects.create(
            client=self.client,
            tariff=tariff_1,
            funds=10000
        )
        self.account_2 = models.Account.objects.create(
            client=self.client,
            tariff=tariff_2,
            funds=10000
        )
        self.credit_tariff = models.TariffCredit.objects.get(
            type='Auto'
        )

    def test_invalid(self):
        bank_account = scripts.bank_max_funds()
        bank = bank_account.client
        with self.assertRaises(ValidationError):
            models.Credit.objects.create(
                client=bank,
                recipient_account=bank_account,
                payment_account=bank_account,
                amount=1000,
                term=12,
                tariff=self.credit_tariff
            )

    def test_str(self):
        credit = models.Credit.objects.create(
            client=self.client,
            payment_account=self.account_1,
            recipient_account=self.account_2,
            tariff=self.credit_tariff,
            amount=10000,
            term=9
        )
        expected_string = '{0} | {1} | {2}'.format(
            credit.client,
            credit.tariff.type,
            credit.remaining_amount
        )
        self.assertEqual(str(credit), expected_string)


class CreditPaymentHistoryTestMethod(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            is_superuser=True,
            username='test',
            first_name='test',
            last_name='test',
            email='test@mail.ru',
            password='test'
        )
        self.client = models.Client.objects.create(
            user=self.user,
            phone_number='89185467890'
        )
        tariff_1 = models.TariffAccount.objects.get(
            type='Deposit'
        )
        tariff_2 = models.TariffAccount.objects.get(
            type='Saving'
        )
        self.account_1 = models.Account.objects.create(
            client=self.client,
            tariff=tariff_1,
            funds=10000
        )
        self.account_2 = models.Account.objects.create(
            client=self.client,
            tariff=tariff_2,
            funds=10000
        )
        tariff = models.TariffCredit.objects.get(
            type='Auto'
        )
        self.credit = models.Credit.objects.create(
            client=self.client,
            payment_account=self.account_1,
            recipient_account=self.account_2,
            tariff=tariff,
            amount=10000,
            term=9
        )

    def test_payment_date(self):
        history = models.CreditPaymentHistory.objects.create(
            credit=self.credit,
            modified=date(2023, 5, 31),
            created=date(2023, 5, 31)
        )
        payment_date = history.payment_date()
        self.assertEqual(payment_date, date(2023, 6, 30))
