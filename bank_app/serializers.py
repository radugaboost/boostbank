"""Serializers for models."""

from . import models
from rest_framework.serializers import ModelSerializer
from django.contrib.auth.models import User


class TariffAccountSerializer(ModelSerializer):
    """Serializer for the TariffAccount model."""

    class Meta:
        model = models.TariffAccount
        fields = ('id', 'type', 'rate', 'created', 'modified')


class TariffCreditSerializer(ModelSerializer):
    """Serializer for the TariffCredit model."""

    class Meta:
        model = models.TariffCredit
        fields = ('id', 'type', 'rate', 'created', 'modified')


class TariffInvestmentSerializer(ModelSerializer):
    """Serializer for the TariffInvestment model."""

    class Meta:
        model = models.TariffInvestment
        fields = ('id', 'type', 'rate', 'created', 'modified')


class UserSerializer(ModelSerializer):
    """Serializer for the User model."""

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'first_name', 'last_name', 'email', 'is_superuser')


class ClientSerializer(ModelSerializer):
    """Serializer for the Client model."""

    class Meta:
        model = models.Client
        fields = ('user', 'phone_number', 'type', 'created', 'modified')


class CreditSerializer(ModelSerializer):
    """Serializer for the Credit model."""

    class Meta:
        model = models.Credit
        fields = (
            'id', 'client', 'amount', 'tariff',
            'recipient_account', 'payment_account', 'term',
            'monthly_payment'
        )


class InvestmentSerializer(ModelSerializer):
    """Serializer for the Investment model."""

    class Meta:
        model = models.Investment
        fields = (
            'id', 'client', 'amount',
            'recipient_account', 'payment_account',
            'tariff', 'created', 'modified', 'term'
        )


class TransactSerializer(ModelSerializer):
    """Serializer for the Transact model."""

    class Meta:
        model = models.Transact
        fields = ('id', 'type', 'sender', 'recipient', 'amount', 'created')


class AccountSerializer(ModelSerializer):
    """Serializer for the Account model."""

    class Meta:
        model = models.Account
        fields = ('id', 'client', 'tariff', 'funds', 'created', 'modified')


class PaymentSerializer(ModelSerializer):
    """Serializer for the Payment model."""

    class Meta:
        model = models.Payment
        fields = ('id', 'sender', 'recipient', 'amount', 'status', 'pay_date', 'callback')


class CreditPaymentHistorySerializer(ModelSerializer):
    """Serializer for the CreditPaymentHistory model."""

    class Meta:
        model = models.CreditPaymentHistory
        fields = ('id', 'credit', 'last_payment')
