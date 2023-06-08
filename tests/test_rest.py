
from django.test import override_settings
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from bank_app import models, config
from bank_app import serializers
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
import json
from django.utils import timezone
from datetime import timedelta
from bank_app.tasks import check_payments, check_credits, check_investments


def create_viewset_tests(
    url: str,
    cls_model: models.models,
    cls_serializer: serializers.ModelSerializer,
    request_content: dict,
    to_change: dict,
):
    class ViewSetTests(APITestCase):

        def setUp(self):
            self.user = User.objects.get(
                username=config.ADMIN_USERNAME
            )
            token = Token.objects.create(user=self.user)
            self.client = APIClient()
            self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
            self.model = cls_model.objects.create(**request_content)

        def test_create_model(self):
            """Test for creating model."""
            response = self.client.post(url, data=request_content)
            serializer = cls_serializer(data=request_content)
            self.assertTrue(serializer.is_valid())
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        def test_get_model(self):
            """Test for getting model."""
            url_to_get = f'{url}{self.model.id}/'
            response = self.client.get(url_to_get)
            serializer = cls_serializer(data=request_content)
            self.assertTrue(serializer.is_valid())
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        def test_update_model(self):
            """Test for updating model."""
            url_to_update = f'{url}{self.model.id}/'
            response = self.client.put(
                url_to_update,
                data=json.dumps(to_change),
                content_type='application/json'
            )
            serializer = cls_serializer(data=to_change)
            self.assertTrue(serializer.is_valid())
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        def test_delete_model(self):
            """Test for deliting model."""
            url_to_delete = f'{url}{self.model.id}/'
            response = self.client.delete(url_to_delete)
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
            self.assertFalse(
                cls_model.objects.filter(id=self.model.id).exists()
            )

    return ViewSetTests


TariffAccountTests = create_viewset_tests(
    '/rest/tariff_account/',
    models.TariffAccount,
    serializers.TariffAccountSerializer,
    {
        "type": "Saving",
        "rate": 10.2
    },
    {
        "type": "Deposit",
        "rate": 15.12
    }
)

TariffCreditTests = create_viewset_tests(
    '/rest/tariff_credit/',
    models.TariffCredit,
    serializers.TariffCreditSerializer,
    {
        "type": "Auto",
        "rate": 11.55
    },
    {
        "type": "Student",
        "rate": 15.12
    }
)

TariffInvestmentTests = create_viewset_tests(
    '/rest/tariff_investment/',
    models.TariffInvestment,
    serializers.TariffInvestmentSerializer,
    {
        "type": "Stock",
        "rate": 11.55
    },
    {
        "type": "Cryptocurrency",
        "rate": 15.12
    }
)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class ClientTest(APITestCase):

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            is_superuser=True,
            username='test',
            first_name='test',
            last_name='test',
            email='test@mail.ru',
            password='test'
        )
        token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        user = User.objects.create_user(
            username='test1',
            first_name='test',
            last_name='test',
            email='test1@mail.ru',
            password='test'
        )
        self.request_data = {
            "user": f'{user.id}',
            "phone_number": "89185413023",
            "type": "Private"
        }
        self.to_change = {
            "phone_number": "89765657890",
            "type": "Bank"
        }
        self.model = models.Client.objects.create(
            user=self.user,
            phone_number="89765657890",
            type='Private'
        )

    def test_create_model(self):
        """Test for creating model."""
        serializer = serializers.ClientSerializer(data=self.request_data)
        self.assertTrue(serializer.is_valid())
        response = self.client.post(
            '/rest/client/',
            data=json.dumps(self.request_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_model(self):
        """Test for getting model."""
        url_to_get = f'/rest/client/{self.model.user_id}/'
        response = self.client.get(url_to_get)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_model(self):
        """Test for updating model."""
        url_to_update = f'/rest/client/{self.model.user_id}/'
        response = self.client.patch(
            url_to_update,
            data=json.dumps(
                self.to_change,
            ),
            content_type='application/json'
        )
        serializer = serializers.ClientSerializer(data=self.to_change, partial=True)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_model(self):
        """Test for deliting model."""
        url_to_delete = f'/rest/client/{self.model.user_id}/'
        response = self.client.delete(url_to_delete)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            models.Client.objects.filter(user_id=self.model.user_id).exists()
        )


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class InvestmentTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            is_superuser=True,
            id=1,
            username='test',
            first_name='test',
            last_name='test',
            email='test@mail.ru',
            password='test'
        )
        token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        client = models.Client.objects.create(
            user=User.objects.create(
                is_superuser=True,
                username='test1',
                first_name='test',
                last_name='test',
                email='test@mail.ru',
                password='test'
            ),
            phone_number="89185643454"
        )
        tariff_account = models.TariffAccount.objects.get(
            type='Deposit'
        )
        account = models.Account.objects.create(
            client=client,
            tariff=tariff_account
        )
        tariff_investment = models.TariffInvestment.objects.get(
            type='Stock'
        )
        self.model = models.Investment.objects.create(
            client=client,
            tariff=tariff_investment,
            recipient_account=account,
            payment_account=account,
            term=1,
            amount=10000
        )
        self.request_data = {
            "client": f'{client.user_id}',
            "tariff": f'{tariff_investment.id}',
            "recipient_account": f'{account.id}',
            "payment_account": f'{account.id}',
            "term": 1,
            "amount": 10000
        }
        self.to_change = {
            "term": 2,
            "amount": 12000
        }

    def test_create_model(self):
        """Test for creating model."""
        response = self.client.post(
            '/rest/investment/',
            data=json.dumps(self.request_data),
            content_type='application/json'
        )
        serializer = serializers.InvestmentSerializer(data=self.request_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_model(self):
        """Test for getting model."""
        url_to_get = f'/rest/investment/{self.model.id}/'
        response = self.client.get(url_to_get)
        check_investments()
        serializer = serializers.InvestmentSerializer(data=self.request_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_for_celery(self):
        """Test celery task for this model."""
        self.model.modified -= timedelta(days=366)
        self.model.save()
        check_investments()
        payment = models.Payment.objects.get(type=config.TYPE_INVESTMENT)
        payment.status = config.PAYMENT_CONFIRMED
        payment.save()
        self.assertTrue(self.model.status, config.PAID_STATUS)

    def test_update_model(self):
        """Test for updating model."""
        url_to_update = f'/rest/investment/{self.model.id}/'
        response = self.client.patch(
            url_to_update,
            data=json.dumps(
                self.to_change,
            ),
            content_type='application/json'
        )
        serializer = serializers.InvestmentSerializer(data=self.to_change, partial=True)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_model(self):
        """Test for deliting model."""
        url_to_delete = f'/rest/investment/{self.model.id}/'
        response = self.client.delete(url_to_delete)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            models.Investment.objects.filter(id=self.model.id).exists()
        )


class CreditTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            is_superuser=True,
            id=1,
            username='test',
            first_name='test',
            last_name='test',
            email='test@mail.ru',
            password='test'
        )
        token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        client = models.Client.objects.create(
            user=User.objects.create(
                is_superuser=True,
                username='test1',
                first_name='test',
                last_name='test',
                email='test@mail.ru',
                password='test'
            ),
            phone_number="89185643454"
        )
        tariff_account = models.TariffAccount.objects.get(
            type='Deposit'
        )
        account = models.Account.objects.create(
            client=client,
            tariff=tariff_account
        )
        tariff_credit = models.TariffCredit.objects.get(
            type='Auto'
        )
        self.model = models.Credit.objects.create(
            client=client,
            tariff=tariff_credit,
            recipient_account=account,
            payment_account=account,
            term=12,
            amount=10000
        )
        self.request_data = {
            "client": f'{client.user_id}',
            "tariff": f'{tariff_credit.id}',
            "recipient_account": f'{account.id}',
            "payment_account": f'{account.id}',
            "term": 12,
            "amount": 10000
        }
        self.to_change = {
            "term": 20,
            "amount": 12000
        }

    def test_create_model(self):
        """Test for creating model."""
        response = self.client.post(
            '/rest/credit/',
            data=json.dumps(self.request_data),
            content_type='application/json'
        )
        serializer = serializers.CreditSerializer(data=self.request_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_model(self):
        """Test for getting model."""
        url_to_get = f'/rest/credit/{self.model.id}/'
        check_credits()
        response = self.client.get(url_to_get)
        serializer = serializers.CreditSerializer(data=self.request_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_model(self):
        """Test for updating model."""
        url_to_update = f'/rest/credit/{self.model.id}/'
        response = self.client.patch(
            url_to_update,
            data=json.dumps(
                self.to_change,
            ),
            content_type='application/json'
        )
        serializer = serializers.CreditSerializer(data=self.to_change, partial=True)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_model(self):
        """Test for deliting model."""
        url_to_delete = f'/rest/credit/{self.model.id}/'
        response = self.client.delete(url_to_delete)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            models.Credit.objects.filter(id=self.model.id).exists()
        )


class TransactTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            is_superuser=True,
            id=1,
            username='test',
            first_name='test',
            last_name='test',
            email='test@mail.ru',
            password='test'
        )
        token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        self.test_client = models.Client.objects.create(
            user=User.objects.create(
                is_superuser=True,
                username='test1',
                first_name='test',
                last_name='test',
                email='test@mail.ru',
                password='test'
            ),
            phone_number="89185643454"
        )
        self.tariff = models.TariffAccount.objects.get(
            type='Deposit'
        )
        self.sender_account = models.Account.objects.create(
            client=self.test_client,
            tariff=self.tariff,
            funds=10000
        )
        self.recipient_account = models.Account.objects.create(
            client=self.test_client,
            tariff=self.tariff,
            funds=10000
        )
        self.model = models.Transact.objects.create(
            sender=self.sender_account,
            recipient=self.recipient_account,
            amount=1000,
            type='Purchase'
        )
        self.request_data = {
            "sender": f'{self.sender_account.id}',
            "recipient": f'{self.recipient_account.id}',
            "amount": 1000,
            "type": "Purchase"
        }
        self.to_change = {
            "amount": 2000,
            "type": "Transfer"
        }

    def test_init_model(self):
        init_sender_funds = self.sender_account.funds
        init_recipient_funds = self.recipient_account.funds
        self.model = models.Transact.objects.create(
            sender=self.sender_account,
            recipient=self.recipient_account,
            amount=1000,
            type='Purchase'
        )
        self.assertTrue(init_sender_funds > self.sender_account.funds)
        self.assertTrue(init_recipient_funds < self.recipient_account.funds)

    def test_create_model(self):
        """Test for creating model."""
        response = self.client.post(
            '/rest/transact/',
            data=json.dumps(self.request_data),
            content_type='application/json'
        )
        serializer = serializers.TransactSerializer(data=self.request_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_model(self):
        """Test for getting model."""
        url_to_get = f'/rest/transact/{self.model.id}/'
        response = self.client.get(url_to_get)
        serializer = serializers.TransactSerializer(data=self.request_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_model(self):
        """Test for updating model."""
        url_to_update = f'/rest/transact/{self.model.id}/'
        response = self.client.patch(
            url_to_update,
            data=json.dumps(
                self.to_change,
            ),
            content_type='application/json'
        )
        serializer = serializers.TransactSerializer(data=self.to_change, partial=True)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_model(self):
        """Test for deliting model."""
        url_to_delete = f'/rest/transact/{self.model.id}/'
        response = self.client.delete(url_to_delete)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            models.Transact.objects.filter(id=self.model.id).exists()
        )


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class PaymentTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            is_superuser=True,
            id=1,
            username='test',
            first_name='test',
            last_name='test',
            email='test@mail.ru',
            password='test'
        )
        token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        self.test_client = models.Client.objects.create(
            user=User.objects.create(
                is_superuser=True,
                username='test1',
                first_name='test',
                last_name='test',
                email='test@mail.ru',
                password='test'
            ),
            phone_number="89185643454"
        )
        self.tariff = models.TariffAccount.objects.get(
            type='Deposit'
        )
        self.sender_account = models.Account.objects.create(
            client=self.test_client,
            tariff=self.tariff,
            funds=10000
        )
        self.recipient_account = models.Account.objects.create(
            client=self.test_client,
            tariff=self.tariff,
            funds=10000
        )
        self.model = models.Payment.objects.create(
            sender=self.sender_account,
            recipient=self.recipient_account,
            amount=1000,
            type='Purchase',
            status='Waiting'
        )
        self.request_data = {
            "sender": f'{self.sender_account.id}',
            "recipient": f'{self.recipient_account.id}',
            "amount": 1000,
            "type": "Purchase",
            "status": "Waiting"
        }
        self.to_change = {
            "amount": 2000,
            "type": "Transfer",
            "status": "Waiting"
        }

    def test_create_model(self):
        """Test for creating model."""
        response = self.client.post(
            '/rest/payment/',
            data=json.dumps(self.request_data),
            content_type='application/json'
        )
        serializer = serializers.PaymentSerializer(data=self.request_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_model(self):
        """Test for getting model."""
        url_to_get = f'/rest/payment/{self.model.id}/'
        check_payments()  # selery task
        response = self.client.get(url_to_get)
        serializer = serializers.PaymentSerializer(data=self.request_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_model(self):
        """Test for updating model."""
        url_to_update = f'/rest/payment/{self.model.id}/'
        response = self.client.patch(
            url_to_update,
            data=json.dumps(
                self.to_change,
            ),
            content_type='application/json'
        )
        serializer = serializers.PaymentSerializer(data=self.to_change, partial=True)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_model(self):
        """Test for deliting model."""
        url_to_delete = f'/rest/payment/{self.model.id}/'
        response = self.client.delete(url_to_delete)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            models.Payment.objects.filter(id=self.model.id).exists()
        )


class AccountTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            is_superuser=True,
            id=1,
            username='test',
            first_name='test',
            last_name='test',
            email='test@mail.ru',
            password='test'
        )
        token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        self.test_client = models.Client.objects.create(
            user=User.objects.create(
                is_superuser=True,
                username='test1',
                first_name='test',
                last_name='test',
                email='test@mail.ru',
                password='test'
            ),
            phone_number="89185643454"
        )
        self.tariff = models.TariffAccount.objects.get(
            type='Deposit'
        )
        self.model = models.Account.objects.create(
            client=self.test_client,
            tariff=self.tariff,
            funds=10000
        )
        self.request_data = {
            "client": f'{self.test_client.user_id}',
            "tariff": f'{self.tariff.id}',
            "funds": 12000
        }
        self.to_change = {
            "funds": 10000
        }

    def test_create_model(self):
        """Test for creating model."""
        response = self.client.post(
            '/rest/account/',
            data=json.dumps(self.request_data),
            content_type='application/json'
        )
        serializer = serializers.AccountSerializer(data=self.request_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_model(self):
        """Test for getting model."""
        url_to_get = f'/rest/account/{self.model.id}/'
        response = self.client.get(url_to_get)
        serializer = serializers.AccountSerializer(data=self.request_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_model(self):
        """Test for updating model."""
        url_to_update = f'/rest/account/{self.model.id}/'
        response = self.client.patch(
            url_to_update,
            data=json.dumps(
                self.to_change,
            ),
            content_type='application/json'
        )
        serializer = serializers.AccountSerializer(data=self.to_change, partial=True)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_model(self):
        """Test for deliting model."""
        url_to_delete = f'/rest/account/{self.model.id}/'
        response = self.client.delete(url_to_delete)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            models.Account.objects.filter(id=self.model.id).exists()
        )


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class CreditPaymentHistoryTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            is_superuser=True,
            id=1,
            username='test',
            first_name='test',
            last_name='test',
            email='test@mail.ru',
            password='test'
        )
        token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        client = models.Client.objects.create(
            user=User.objects.create(
                is_superuser=True,
                username='test1',
                first_name='test',
                last_name='test',
                email='test@mail.ru',
                password='test'
            ),
            phone_number="89185643454"
        )
        tariff_account = models.TariffAccount.objects.get(
            type='Deposit'
        )
        account = models.Account.objects.create(
            client=client,
            tariff=tariff_account
        )
        tariff_credit = models.TariffCredit.objects.get(
            type='Auto'
        )
        credit = models.Credit.objects.create(
            client=client,
            tariff=tariff_credit,
            recipient_account=account,
            payment_account=account,
            term=12,
            amount=10000
        )
        self.model = models.CreditPaymentHistory.objects.get(
            credit=credit
        )
        self.request_data = {
            "credit": f'{credit.id}',
            "last_payment": f'{timezone.now()}'
        }
        self.to_change = {
            "last_payment": f'{timezone.now() + timedelta(minutes=5)}'
        }

    def test_create_model(self):
        """Test for creating model."""
        response = self.client.post(
            '/rest/credit_payment_history/',
            data=json.dumps(self.request_data),
            content_type='application/json'
        )
        serializer = serializers.CreditPaymentHistorySerializer(data=self.request_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_model(self):
        """Test for getting model."""
        url_to_get = f'/rest/credit_payment_history/{self.model.id}/'
        response = self.client.get(url_to_get)
        serializer = serializers.CreditPaymentHistorySerializer(data=self.request_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_model_query(self):
        """Test for getting model."""
        url_to_get = f'/rest/credit_payment_history/?id={self.model.id}'
        response = self.client.get(url_to_get)
        serializer = serializers.CreditPaymentHistorySerializer(data=self.request_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_model(self):
        """Test for updating model."""
        url_to_update = f'/rest/credit_payment_history/{self.model.id}/'
        response = self.client.patch(
            url_to_update,
            data=json.dumps(
                self.to_change,
            ),
            content_type='application/json'
        )
        serializer = serializers.CreditPaymentHistorySerializer(data=self.to_change, partial=True)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_for_celery(self):
        """Test selery task for this model."""
        self.model.modified -= timedelta(days=15)
        credit = self.model.credit
        credit.remaining_amount = credit.monthly_payment
        credit.save()
        self.model.save()
        check_credits()
        payment = models.Payment.objects.get(
            type=config.TYPE_CREDIT
        )
        payment.status = config.PAYMENT_CONFIRMED
        payment.save()
        self.assertTrue(self.model.modified.date(), timezone.now().date())

    def test_for_celery_callback(self):
        """Test selery callback for this model."""
        self.model.modified -= timedelta(days=15)
        self.model.save()
        check_credits()
        payment = models.Payment.objects.get(
            type=config.TYPE_CREDIT
        )
        payment.status = config.PAYMENT_CONFIRMED
        payment.save()
        self.assertTrue(self.model.modified.date(), timezone.now().date())

    def test_delete_model(self):
        """Test for deliting model."""
        url_to_delete = f'/rest/credit_payment_history/{self.model.id}/'
        response = self.client.delete(url_to_delete)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            models.CreditPaymentHistory.objects.filter(id=self.model.id).exists()
        )
