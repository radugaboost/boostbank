"""Scripts for work with models."""

from . import config, models
from django.db.models import Min, Max
from django.db import transaction
import calendar
from datetime import datetime, date


def date_this_month(check_date) -> bool:
    """Check if the date is in the current month.

    Args:
        check_date: The date you want to check.

    Returns:
        bool: True if check_date is in the current month.
    """
    now = datetime.now()
    year = now.year
    month = now.month
    _, num_days = calendar.monthrange(year, month)
    first_day = date(year, month, 1)
    last_day = date(year, month, num_days)
    condition1 = check_date >= first_day
    condition2 = check_date <= last_day
    return condition1 and condition2


def bank_min_funds() -> models.Account:
    """Method returns bank account with minimum balance.

    Returns:
        models.Account: bank account.
    """
    bank = models.Client.objects.get(type=config.TYPE_BANK)
    bank_accounts = models.Account.objects.filter(client=bank)
    min_funds = bank_accounts.aggregate(min_funds=Min('funds'))['min_funds']
    return bank_accounts.filter(funds=min_funds).first()


def bank_max_funds() -> models.Account:
    """Method returns bank account with maximum balance.

    Returns:
        models.Account: bank account.
    """
    bank = models.Client.objects.get(type=config.TYPE_BANK)
    bank_accounts = models.Account.objects.filter(client=bank)
    max_funds = bank_accounts.aggregate(max_funds=Max('funds'))['max_funds']
    return bank_accounts.filter(funds=max_funds).first()


def create_transact(
    sender: models.Account,
    recipient: models.Account,
    amount: int,
    transact_type: str
) -> None:
    """Create a new transaction.

    Args:
        sender: The sender account.
        recipient: The recipient account.
        amount: The transaction amount.
        transact_type: The transaction type.
    """
    with transaction.atomic():
        transact = models.Transact.objects.create(
            sender=sender,
            recipient=recipient,
            amount=amount,
            type=transact_type
        )
        transact.save()


def make_payment(
    payment: models.Payment
) -> None:
    """Changes the payment status and creates a transaction.

    Args:
        payment: The payment object.
    """
    with transaction.atomic():
        create_transact(
            sender=payment.sender,
            recipient=payment.recipient,
            amount=payment.amount,
            type=payment.type
        )
        payment.status = config.PAYMENT_CONFIRMED
        payment.save()


def create_credit(
    client: models.Client,
    recipient: models.Account,
    payment: models.Account,
    amount: int,
    tariff: models.TariffCredit,
    term: int,
) -> models.Credit:
    """Create a new credit.

    Args:
        client: The client for whom the credit is created.
        recipient: The recipient account for the credit.
        payment: The payment account for the credit.
        amount: The amount of the credit.
        tariff: The credit tariff.
        term: The term of the credit.

    Returns:
        The created Credit object.
    """
    with transaction.atomic():
        credit = models.Credit.objects.create(
            client=client,
            recipient_account=recipient,
            payment_account=payment,
            amount=amount,
            term=term,
            tariff=tariff
        )
        credit.save()
    return credit


def create_investment(
    client: models.Client,
    amount: int,
    recipient: models.Account,
    payment: models.Account,
    term: int,
    tariff: models.TariffInvestment
) -> models.Investment:
    """Create a new investment.

    Args:
        client: The client associated with the investment.
        amount: The amount of the investment.
        recipient: The recipient account for the investment.
        payment: The payment account for the investment.
        term: The term of the investment.
        tariff: The tariff for the investment.

    Returns:
        models.Investment: The created investment object.
    """
    with transaction.atomic():
        investment = models.Investment.objects.create(
            client=client,
            amount=amount,
            recipient_account=recipient,
            payment_account=payment,
            term=term,
            tariff=tariff
        )
        investment.calculate_debt()
        investment.save()
    return investment


def model_exists(
    model: models.models,
    field_name: str,
    field_value: str
) -> models.models or None:
    """Check if a model with the given field value exists.

    Args:
        model: The model to be checked.
        field_name: The name of the field to be checked.
        field_value: The value of the field to be checked.

    Returns:
        models.models or None: The first matching model instance if exists, None otherwise.
    """
    return model.objects.filter(**{field_name: field_value}).first()


def bank_solvency_check(amount: int) -> bool:
    """Check if the bank has sufficient funds.

    Args:
        amount: The amount of payment.

    Returns:
        bool: True if the bank has sufficient funds, False otherwise.
    """
    bank = models.Client.objects.get(type=config.TYPE_BANK)
    bank_accounts = models.Account.objects.filter(client=bank)
    for bank_account in bank_accounts:
        if bank_account.funds >= amount:
            return True
    return False
