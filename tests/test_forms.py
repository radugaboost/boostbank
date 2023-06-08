from django.test import TestCase
from bank_app import models, config, forms, scripts
from django.contrib.auth.models import User
from uuid import uuid4


class TransferFromTest(TestCase):

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

    def test_form_valid(self):
        request_data = {
            'amount': 1000,
            'sender_account': self.account_1.id,
            'recipient_account': self.account_2.id
        }
        form = forms.TransferFundsForm(request_data, initial={'client': self.client})
        self.assertTrue(form.is_valid())

    def test_the_same_account(self):
        request_data = {
            'amount': 1000,
            'sender_account': self.account_1.id,
            'recipient_account': self.account_1.id
        }
        form = forms.TransferFundsForm(request_data, initial={'client': self.client})
        self.assertFalse(form.is_valid())

    def test_insufficient_funds(self):
        request_data = {
            'amount': 100000,
            'sender_account': self.account_2.id,
            'recipient_account': self.account_1.id
        }
        form = forms.TransferFundsForm(request_data, initial={'client': self.client})
        self.assertFalse(form.is_valid())

    def test_not_owner(self):
        bank_account = scripts.bank_max_funds()
        request_data = {
            'amount': 100000,
            'sender_account': bank_account.id,
            'recipient_account': self.account_1.id
        }
        form = forms.TransferFundsForm(request_data, initial={'client': self.client})
        self.assertFalse(form.is_valid())

    def test_account_not_exists(self):
        request_data = {
            'amount': 100000,
            'sender_account': uuid4(),
            'recipient_account': uuid4()
        }
        form = forms.TransferFundsForm(request_data, initial={'client': self.client})
        self.assertFalse(form.is_valid())


class CreditFormTest(TestCase):

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
        self.credit_tariff = models.TariffCredit.objects.get(
            type='Auto'
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
        request_data = {
            'amount': 10000,
            'term': 12,
            'credit_tariff': self.credit_tariff.type,
            'recipient_account': self.account_1.id,
            'payment_account': self.account_1.id
        }
        form = forms.CreditForm(request_data, initial={'client': self.client})
        self.assertTrue(form.is_valid())

    def test_bank_solvency(self):
        bank_account = scripts.bank_max_funds()
        bank_account.funds = 100
        bank_account.save()
        request_data = {
            'amount': 10000,
            'term': 12,
            'credit_tariff': self.credit_tariff.type,
            'recipient_account': self.account_1.id,
            'payment_account': self.account_1.id
        }
        form = forms.CreditForm(request_data, initial={'client': self.client})
        self.assertFalse(form.is_valid())

    def test_credit_from_itself(self):
        bank_account = scripts.bank_max_funds()
        request_data = {
            'amount': 10000,
            'term': 12,
            'credit_tariff': self.credit_tariff.type,
            'recipient_account': bank_account.id,
            'payment_account': bank_account.id
        }
        form = forms.CreditForm(request_data, initial={'client': self.client})
        self.assertFalse(form.is_valid())

    def test_not_owner(self):
        bank_account = scripts.bank_max_funds()
        request_data = {
            'amount': 10000,
            'term': 12,
            'credit_tariff': self.credit_tariff.type,
            'recipient_account': self.account_1.id,
            'payment_account': bank_account.id
        }
        form = forms.CreditForm(request_data, initial={'client': self.client})
        self.assertFalse(form.is_valid())

    def test_not_exists_account(self):
        request_data = {
            'amount': 10000,
            'term': 12,
            'credit_tariff': self.credit_tariff.type,
            'recipient_account': uuid4(),
            'payment_account': uuid4()
        }
        form = forms.CreditForm(request_data, initial={'client': self.client})
        self.assertFalse(form.is_valid())

    def test_no_such_tariff(self):
        credit_trf = models.TariffCredit.objects.get(
            type='Business'
        )
        credit_trf.delete()
        request_data = {
            'amount': 10000,
            'term': 12,
            'credit_tariff': 'Business',
            'recipient_account': self.account_1.id,
            'payment_account': self.account_1.id
        }
        form = forms.CreditForm(request_data, initial={'client': self.client})
        self.assertFalse(form.is_valid())

    def test_max_number(self):
        for _ in range(config.MAX_NUMBER_OF_CREDITS):
            credit = models.Credit.objects.create(
                client=self.client,
                recipient_account=self.account_1,
                payment_account=self.account_2,
                tariff=self.credit_tariff,
                amount=10000,
                term=12
            )
            credit.save()
        request_data = {
            'amount': 10000,
            'term': 12,
            'credit_tariff': self.credit_tariff.type,
            'recipient_account': self.account_1.id,
            'payment_account': self.account_1.id
        }
        form = forms.CreditForm(request_data, initial={'client': self.client})
        self.assertFalse(form.is_valid())


class InvestmentFormTest(TestCase):

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
        self.investment_tariff = models.TariffInvestment.objects.get(
            type='Stock'
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
        request_data = {
            'amount': 10000,
            'term': 1,
            'invest_tariff': self.investment_tariff.type,
            'recipient_account': self.account_1.id,
            'payment_account': self.account_1.id
        }
        form = forms.InvestmentForm(request_data, initial={'client': self.client})
        self.assertTrue(form.is_valid())

    def test_no_such_tariff(self):
        invest_trf = models.TariffInvestment.objects.get(
            type='Cryptocurrency'
        )
        invest_trf.delete()
        request_data = {
            'amount': 10000,
            'term': 1,
            'invest_tariff': 'Cryptocurrency',
            'recipient_account': self.account_1.id,
            'payment_account': self.account_1.id
        }
        form = forms.InvestmentForm(request_data, initial={'client': self.client})
        self.assertFalse(form.is_valid())

    def test_bank_for_itself(self):
        bank_account = scripts.bank_max_funds()
        request_data = {
            'amount': 10000,
            'term': 1,
            'invest_tariff': self.investment_tariff.type,
            'recipient_account': bank_account.id,
            'payment_account': bank_account.id
        }
        form = forms.InvestmentForm(request_data, initial={'client': self.client})
        self.assertFalse(form.is_valid())

    def test_account_not_exists(self):
        request_data = {
            'amount': 10000,
            'term': 1,
            'invest_tariff': self.investment_tariff.type,
            'recipient_account': uuid4(),
            'payment_account': uuid4()
        }
        form = forms.InvestmentForm(request_data, initial={'client': self.client})
        self.assertFalse(form.is_valid())

    def test_not_owner(self):
        bank_account = scripts.bank_max_funds()
        request_data = {
            'amount': 10000,
            'term': 1,
            'invest_tariff': self.investment_tariff.type,
            'recipient_account': self.account_1.id,
            'payment_account': bank_account.id
        }
        form = forms.InvestmentForm(request_data, initial={'client': self.client})
        self.assertFalse(form.is_valid())

    def test_insufficient_funds(self):
        request_data = {
            'amount': 10000000,
            'term': 1,
            'invest_tariff': self.investment_tariff.type,
            'recipient_account': self.account_1.id,
            'payment_account': self.account_1.id
        }
        form = forms.InvestmentForm(request_data, initial={'client': self.client})
        self.assertFalse(form.is_valid())

    def test_invest_tariff_exists(self):
        investment = models.Investment.objects.create(
            client=self.client,
            recipient_account=self.account_1,
            payment_account=self.account_1,
            term=1,
            amount=10000,
            tariff=self.investment_tariff
        )
        investment.save()
        request_data = {
            'amount': 1000,
            'term': 1,
            'invest_tariff': self.investment_tariff.type,
            'recipient_account': self.account_1.id,
            'payment_account': self.account_1.id
        }
        form = forms.InvestmentForm(request_data, initial={'client': self.client})
        self.assertFalse(form.is_valid())


class PaymentFormTest(TestCase):

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
        tariff = models.TariffAccount.objects.get(
            type='Deposit'
        )
        self.account = models.Account.objects.create(
            client=self.client,
            tariff=tariff,
            funds=10000
        )
        self.bank_account = scripts.bank_max_funds()
        self.payment = models.Payment.objects.create(
            sender=self.account,
            recipient=self.bank_account,
            amount=1000
        )

    def test_valid(self):
        request_data = {
            'sender_account': self.account.id
        }
        form = forms.PaymentForm(request_data, initial={'client': self.client, 'payment': self.payment})
        self.assertTrue(form.is_valid())

    def test_account_not_exists(self):
        request_data = {
            'sender_account': uuid4()
        }
        form = forms.PaymentForm(request_data, initial={'client': self.client, 'payment': self.payment})
        self.assertFalse(form.is_valid())

    def test_not_owner(self):
        bank_account = scripts.bank_max_funds()
        request_data = {
            'sender_account': bank_account.id
        }
        form = forms.PaymentForm(request_data, initial={'client': self.client, 'payment': self.payment})
        self.assertFalse(form.is_valid())

    def test_insufficient_funds(self):
        self.account.funds = 0
        self.account.save()
        request_data = {
            'sender_account': self.account.id
        }
        form = forms.PaymentForm(request_data, initial={'client': self.client, 'payment': self.payment})
        self.assertFalse(form.is_valid())


class TariffAccountFormTest(TestCase):
    def setUp(self):
        self.tariff = models.TariffAccount.objects.get(
            type='Saving'
        )
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

    def test_valid(self):
        request_data = {
            'account_tariff': self.tariff.type
        }
        form = forms.TariffAccountForm(request_data, initial={'client': self.client})
        self.assertTrue(form.is_valid())

    def test_no_such_tariff(self):
        tariff = models.TariffAccount.objects.get(
            type='Current'
        )
        tariff.type = 'Deposit'
        tariff.save()
        request_data = {
            'account_tariff': 'Current'
        }
        form = forms.TariffAccountForm(request_data, initial={'client': self.client})
        self.assertFalse(form.is_valid())

    def test_account_tariff_exists(self):
        account = models.Account.objects.create(
            client=self.client,
            tariff=self.tariff
        )
        account.save()
        request_data = {
            'account_tariff': self.tariff.type
        }
        form = forms.TariffAccountForm(request_data, initial={'client': self.client})
        self.assertFalse(form.is_valid())


class ProfilePaymentFormTest(TestCase):

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
        self.investment_tariff = models.TariffInvestment.objects.get(
            type='Stock'
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
        payment = models.Payment.objects.create(
            sender=self.account_1,
            recipient=self.account_2,
            amount=1000
        )
        payment.save()
        request_data = {
            'payment': payment.id
        }
        form = forms.ProfilePaymentForm(request_data)
        self.assertTrue(form.is_valid())

    def test_payment_not_exists(self):
        request_data = {
            'payment': uuid4()
        }
        form = forms.ProfilePaymentForm(request_data)
        self.assertFalse(form.is_valid())

    def test_insufficient_funds(self):
        payment = models.Payment.objects.create(
            sender=self.account_1,
            recipient=self.account_2,
            amount=1000000
        )
        payment.save()
        request_data = {
            'payment': payment.id
        }
        form = forms.ProfilePaymentForm(request_data)
        self.assertFalse(form.is_valid())
