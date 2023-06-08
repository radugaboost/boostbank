"""Signals for handle changes in objects."""
from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from . import models, config, scripts
import requests
import logging
from django.utils import timezone
from django.db import transaction
from random import randint
from django.contrib.auth.models import User

logging.basicConfig(level=logging.INFO, filename=config.FILENAME_CALLBACK_ERRORS, filemode="w")


def create_tariffs(model: models.models, types: tuple):
    """This method creates tariffs.

    Args:
        model (models.models): model of tariff.
        types (tuple): tuple of tariff types.
    """
    for tariff_type in types:
        with transaction.atomic():
            tariff = model.objects.create(
                type=tariff_type[0],
                rate=randint(*config.INIT_PERCENTAGE_INTERVAL)
            )
            tariff.save()


@receiver(post_migrate)
def create_initial_models(sender, **kwargs):
    """This method creates initial models when migrating models.

    Args:
        sender (app): this application.
        kwargs (_type_): some keyword.
    """
    if sender.name == 'bank_app':

        if not models.TariffAccount.objects.exists():
            create_tariffs(models.TariffAccount, models.account_types)

        if not models.TariffCredit.objects.exists():
            create_tariffs(models.TariffCredit, models.credit_types)

        if not models.TariffInvestment.objects.exists():
            create_tariffs(models.TariffInvestment, models.invest_types)

        if User.objects.filter(is_superuser=True).count() == 0:
            with transaction.atomic():
                admin = User.objects.create_superuser(
                    username=config.ADMIN_USERNAME,
                    first_name=config.ADMIN_FIRST_NAME,
                    last_name=config.ADMIN_LAST_NAME,
                    email=config.ADMIN_EMAIL,
                    password=config.ADMIN_PASSWORD
                )
                admin.save()
                bank = models.Client.objects.create(
                    user=admin,
                    type=config.TYPE_BANK,
                    phone_number=config.ADMIN_PHONE_NUMBER
                )
                bank.save()
                bank_account = models.Account.objects.create(
                    client=bank,
                    tariff=models.TariffAccount.objects.all().first(),
                    funds=config.INITIAL_BANK_FUNDS
                )
                bank_account.save()


@receiver(post_save, sender=models.Payment)
def handle_payment(instance: models.Payment, **kwargs):
    """This method implements a callback to the recipient.

    Args:
        instance (models.Payment): the object that was saved.
        kwargs (_type_): some keyword.
    """
    condition_list = [config.PAYMENT_CANCELLED, config.PAYMENT_CONFIRMED]
    if instance.status in condition_list:
        callback = instance.callback
        if callback:
            if callback.get('url'):
                try:
                    requests.patch(
                        url=callback.get('url'),
                        headers=callback.get('headers'),
                        json={'status': instance.status}
                    )
                except Exception as error:
                    logging.info('{0}: {1} [{2}]').format(instance.id, error, timezone.now())

            if callback.get('credit_payment_history_id') and instance.status == config.PAYMENT_CONFIRMED:
                history = models.CreditPaymentHistory.objects.get(
                    id=callback.get('credit_payment_history_id')
                )
                credit = models.Credit.objects.get(
                    id=callback.get('credit_id')
                )
                credit.remaining_amount -= credit.monthly_payment
                if credit.remaining_amount == 0:
                    credit.status = config.PAID_STATUS
                    history.delete()
                else:
                    history.last_payment = timezone.now()
                    history.save()

                credit.save()

            if callback.get('investment_id') and instance.status == config.PAYMENT_CONFIRMED:
                investment = models.Investment.objects.get(
                    id=callback.get('investment_id')
                )
                investment.status = config.PAID_STATUS
                investment.save()


@receiver(post_save, sender=models.Transact)
def handle_new_transact(instance: models.Transact, created, **kwargs):
    """Looking forward to saving the new transact.

    Args:
        instance (models.Transact): the object that was saved
        created (timezone): a keyword that determines whether this object is new.
        kwargs (_type_): some keyword.
    """
    if created:
        sender = instance.sender
        recipient = instance.recipient
        sender.funds -= instance.amount
        recipient.funds += instance.amount
        sender.save()
        recipient.save()


@receiver(post_save, sender=models.Credit)
def handle_new_credit(instance: models.Credit, created, **kwargs):
    """Looking forward to saving the new credit.

    Args:
        instance (models.Credit): the object that was saved.
        created (timezone): a keyword that determines whether this object is new.
        kwargs (_type_): some keyword.
    """
    if created:
        bank_account = scripts.bank_max_funds()
        scripts.create_transact(
            sender=bank_account,
            recipient=instance.recipient_account,
            amount=instance.amount,
            transact_type=config.TYPE_CREDIT
        )
        payment_history = models.CreditPaymentHistory.objects.create(
            credit=instance
        )
        payment_history.save()


@receiver(post_save, sender=models.Investment)
def handle_new_investment(instance: models.Investment, created, **kwargs):
    """Looking forward to saving the new investment.

    Args:
        instance (models.Investment): the object that was saved
        created (timezone): a keyword that determines whether this object is new.
        kwargs (_type_): some keyword.
    """
    if created:
        bank_account = scripts.bank_min_funds()
        scripts.create_transact(
            sender=instance.payment_account,
            recipient=bank_account,
            amount=instance.amount,
            transact_type=config.TYPE_INVESTMENT
        )
