"""Tasks for celery."""
from bank.celery import app
from bank_app import models
from bank_app import config
from django.utils import timezone
from django.db import transaction
from . import scripts


@app.task
def check_credits():
    """Celery task for checking and processing credits.

    Retrieves all credit objects.
    Checks if the payment history's payment date matches the current date.
    Creates a payment and updates the payment history if a match is found.

    """
    now = timezone.now()
    credits = models.Credit.objects.all()
    for credit in credits:
        payment_history = models.CreditPaymentHistory.objects.get(credit=credit)
        if payment_history.payment_date() == now.date():
            with transaction.atomic():
                payment = models.Payment.objects.create(
                    sender=credit.payment_account,
                    recipient=scripts.bank_min_funds(),
                    amount=credit.monthly_payment,
                    pay_date=now + timezone.timedelta(days=config.PAY_DATE_DAYS),
                    type=config.TYPE_CREDIT,
                    callback={
                        'credit_payment_history_id': '{0}'.format(payment_history.id),
                        'credit_id': '{0}'.format(credit.id)
                    }
                )
                payment.save()
                payment_history.modified = now
                payment_history.save()


@app.task
def check_investments():
    """Celery task for checking and processing investments.

    Retrieves all active investment objects.
    Checks if the investment needs to be repaid.
    Creates a payment if repayment is needed.

    """
    investments = models.Investment.objects.filter(
        status=config.ACTIVE_STATUS
    )
    for investment in investments:
        if investment.need_repay():
            bank_account = scripts.bank_max_funds()
            with transaction.atomic():
                payment = models.Payment.objects.create(
                    sender=bank_account,
                    recipient=investment.recipient_account,
                    amount=investment.remaining_amount,
                    pay_date=timezone.now() + timezone.timedelta(days=config.PAY_DATE_DAYS),
                    type=config.TYPE_INVESTMENT,
                    callback={
                        'investment_id': '{0}'.format(investment.id)
                    }
                )
                payment.save()


@app.task
def check_payments():
    """Celery task for checking and cancelling payments.

    Retrieves all payments with a pay_date earlier than or equal to the current time
    and with a status of PAYMENT_WAITING.
    Cancels the payments by updating their status to PAYMENT_CANCELLED.

    """
    payments = models.Payment.objects.filter(
        pay_date__lte=timezone.now(),
        status=config.PAYMENT_WAITING
    )
    for payment in payments:
        with transaction.atomic():
            payment.status = config.PAYMENT_CANCELLED
            payment.save()
