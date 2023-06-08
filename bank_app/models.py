"""Models for bank app."""
from django.db import models
from uuid import uuid4
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.conf.global_settings import AUTH_USER_MODEL
from django.utils import timezone
from . import config
import calendar
from datetime import date


class UUIDMixin(models.Model):
    """Mixin class for adding a UUID primary key field to a model.

    Attributes:
        id: UUIDField representing the primary key.
    """

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    class Meta:
        abstract = True


class CreatedMixin(models.Model):
    """Mixin class for adding a 'created' field to a model.

    Attributes:
        created: DateTimeField representing the creation timestamp.
    """

    created = models.DateTimeField(
        blank=True, null=False,
        default=timezone.now,
        validators=[MaxValueValidator(timezone.now)]
    )

    class Meta:
        abstract = True


class ModifiedMixin(models.Model):
    """Mixin class for adding a 'modified' field to a model.

    Attributes:
        modified: DateTimeField representing the last modification timestamp.
    """

    modified = models.DateTimeField(
        blank=True,
        null=False,
        default=timezone.now,
        validators=[MaxValueValidator(timezone.now)]
    )

    class Meta:
        abstract = True


class Account(UUIDMixin, CreatedMixin, ModifiedMixin):
    """Model representing an account.

    Attributes:
        client (models.ForeignKey): ForeignKey to the associated client.
        tariff (models.ForeignKey): ForeignKey to the associated account tariff.
        funds (models.DecimalField): DecimalField representing the funds available in the account.
    """

    client = models.ForeignKey('Client', models.DO_NOTHING, blank=True, null=False)
    tariff = models.ForeignKey('TariffAccount', models.DO_NOTHING, blank=True, null=False)
    funds = models.DecimalField(
        max_digits=config.DECIMAL_MAX_DIGITS,
        decimal_places=config.DECIMAL_PLACES,
        blank=True,
        null=True,
        default=config.INIT_ACCOUNT_BALANCE
    )

    def __str__(self) -> str:
        """Return a string representation of the account."""
        return '{0} | ${1}'.format(self.tariff.type, self.funds)

    class Meta:
        db_table = 'account'


client_types = (
    ('Private', 'Private'),
    ('Bank', 'Bank')
)


phone_regex = RegexValidator(
    regex=r'^8\d{10}$',
    message=config.PHONE_NUMBER_ERROR
)


class Client(CreatedMixin, ModifiedMixin):
    """Model representing a client.

    Attributes:
        user (models.OneToOneField): OneToOneField to the associated user.
        phone_number (models.CharField): CharField representing the client's phone number.
        type (models.CharField): CharField representing the client's type.
    """

    user = models.OneToOneField(AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True)
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=config.MAX_PHONE_LENGTH,
        blank=True,
        null=False
    )
    type = models.CharField(
        choices=client_types,
        default=config.TYPE_PRIVATE,
        blank=True,
        null=False,
        max_length=config.MAX_STATUS_TYPE_LENGTH
    )

    def __str__(self):
        """Return a string representation of the client."""
        return '{0} {1} [{2}]'.format(self.user.first_name, self.user.last_name, self.user.id)

    class Meta:
        db_table = 'client'


pay_statuses = (
    ('Active', 'Active'),
    ('Paid', 'Paid')
)


class Credit(UUIDMixin, CreatedMixin, ModifiedMixin):
    """Model representing a credit.

    Attributes:
        client (models.ForeignKey): ForeignKey to the associated client.
        recipient_account (models.ForeignKey): ForeignKey to the recipient account.
        payment_account (models.ForeignKey): ForeignKey to the payment account.
        amount (models.DecimalField): DecimalField representing the credit amount.
        tariff (models.ForeignKey): ForeignKey to the credit tariff.
        remaining_amount (models.DecimalField): DecimalField representing the remaining amount.
        term (models.IntegerField): IntegerField representing the credit term.
        monthly_payment (models.DecimalField): DecimalField representing the monthly payment.
        status (models.CharField): CharField representing the credit status.
    """

    client = models.ForeignKey(Client, models.DO_NOTHING, blank=True, null=False)
    recipient_account = models.ForeignKey(
        Account,
        models.DO_NOTHING,
        blank=True,
        null=False,
        related_name='credit_recipient'
    )
    payment_account = models.ForeignKey(
        Account,
        models.DO_NOTHING,
        blank=True,
        null=False,
        related_name='payment_account'
    )
    amount = models.DecimalField(
        max_digits=config.DECIMAL_MAX_DIGITS,
        decimal_places=config.DECIMAL_PLACES,
        blank=True,
        null=True,
        validators=[
            MinValueValidator(config.MIN_CREDIT_VALUE),
            MaxValueValidator(config.MAX_CREDIT_VALUE)
        ]
    )
    tariff = models.ForeignKey('TariffCredit', models.DO_NOTHING, blank=True, null=False)
    remaining_amount = models.DecimalField(
        max_digits=config.DECIMAL_MAX_DIGITS,
        decimal_places=config.DECIMAL_PLACES,
        blank=True,
        null=True
    )
    term = models.IntegerField(
        blank=True,
        null=True,
        validators=[
            MinValueValidator(config.MIN_CREDIT_TERM),
            MaxValueValidator(config.MAX_CREDIT_TERM)
        ]
    )
    monthly_payment = models.DecimalField(
        max_digits=config.DECIMAL_MAX_DIGITS,
        decimal_places=config.DECIMAL_PLACES,
        blank=True,
        null=True
    )
    status = models.CharField(
        choices=pay_statuses,
        default=config.ACTIVE_STATUS,
        blank=True,
        null=False,
        max_length=config.MAX_STATUS_TYPE_LENGTH
    )

    def __str__(self) -> str:
        """Return a string representation of the credit."""
        return '{0} | {1} | {2}'.format(self.client, self.tariff.type, self.remaining_amount)

    def calculate_debt(self):
        """Calculate the monthly payment and remaining amount of the credit."""
        rate = (self.tariff.rate / 100) / 12
        self.monthly_payment = round((self.amount * rate / (1 - (1 + rate) ** (-self.term))), config.DECIMAL_PLACES)
        self.remaining_amount = round((self.monthly_payment * self.term), config.DECIMAL_PLACES)

    def clean(self):
        """Perform model validation.

        Raises:
            ValidationError: if credit client is bank
        """
        recipient_type = self.recipient_account.client.type == config.TYPE_BANK
        payment_type = self.payment_account.client.type == config.TYPE_BANK
        if recipient_type or payment_type:
            raise ValidationError(config.BANK_CREDIT_ERROR)

    def save(self, *args, **kwargs):
        """Override the save method to update the fields and perform validation.

        Args:
            args (_type_): some argument.
            kwargs (_type_): some keyword.
        """
        self.full_clean()
        if not self.monthly_payment:
            self.calculate_debt()
        self.modified = timezone.now()
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'credit'


class CreditPaymentHistory(UUIDMixin, CreatedMixin, ModifiedMixin):
    """Model representing the payment history of a credit.

    Attributes:
        credit (models.ForeignKey): ForeignKey to the associated credit.
        last_payment (models.DateTimeField): DateTimeField representing the last payment date.
    """

    credit = models.ForeignKey(Credit, on_delete=models.CASCADE, blank=True, null=False)
    last_payment = models.DateTimeField(default=timezone.now, null=False, blank=True)

    def payment_date(self):
        """Calculate and return the payment date based on the created and modified dates.

        Returns:
            date: The calculated payment date.
        """
        payment_day = self.created.day
        payment_month = self.modified.month + 1 if self.modified.month < 12 else 1
        payment_year = self.modified.year
        _, last_day = calendar.monthrange(payment_year, payment_month)
        if payment_day > last_day:
            return date(payment_year, payment_month, last_day)
        return date(payment_year, payment_month, payment_day)

    class Meta:
        db_table = 'credit_payment_history'


class Investment(UUIDMixin, CreatedMixin, ModifiedMixin):
    """Model representing an investment.

    Attributes:
        client (models.ForeignKey): ForeignKey to the associated client.
        amount (models.DecimalField): DecimalField representing the investment amount.
        tariff (models.ForeignKey): ForeignKey to the associated investment tariff.
        recipient_account (models.ForeignKey): ForeignKey to the recipient account.
        payment_account (models.ForeignKey): ForeignKey to the payment account.
        remaining_amount (models.DecimalField): DecimalField representing the remaining investment amount.
        term (models.IntegerField): IntegerField representing the investment term.
        monthly_payment (models.DecimalField): DecimalField representing the monthly payment.
        status (models.CharField): CharField representing the status of the investment.
    """

    client = models.ForeignKey(Client, models.DO_NOTHING, blank=True, null=False)
    amount = models.DecimalField(
        max_digits=config.DECIMAL_MAX_DIGITS,
        decimal_places=config.DECIMAL_PLACES,
        blank=True,
        null=False,
        validators=[
            MinValueValidator(config.MIN_INVESTMENT_VALUE),
            MaxValueValidator(config.MAX_INVESTMENT_VALUE)
        ]
    )
    tariff = models.ForeignKey('TariffInvestment', models.DO_NOTHING, blank=True, null=False)
    recipient_account = models.ForeignKey(
        Account,
        models.DO_NOTHING,
        blank=True,
        null=False,
        related_name='investment_recipient'
    )
    payment_account = models.ForeignKey(
        Account,
        models.DO_NOTHING,
        blank=True,
        null=False,
        related_name='investment_payment'
    )
    remaining_amount = models.DecimalField(
        max_digits=config.DECIMAL_MAX_DIGITS,
        decimal_places=config.DECIMAL_PLACES,
        blank=True,
        null=True
    )
    term = models.IntegerField(
        blank=True,
        null=False,
        validators=[
            MinValueValidator(config.MIN_INVESTMENT_TERM),
            MaxValueValidator(config.MAX_INVESTMENT_TERM)
        ]
    )
    monthly_payment = models.DecimalField(
        max_digits=config.DECIMAL_MAX_DIGITS,
        decimal_places=config.DECIMAL_PLACES,
        blank=True,
        null=True
    )
    status = models.CharField(
        choices=pay_statuses,
        default=config.ACTIVE_STATUS,
        blank=True,
        null=False,
        max_length=config.MAX_STATUS_TYPE_LENGTH
    )

    def __str__(self) -> str:
        """Return a string representation of the investment."""
        return '{0} | {1} | {2}'.format(self.client, self.tariff.type, self.remaining_amount)

    def calculate_debt(self):
        """Calculate the remaining amount and monthly payment based on the investment amount and term."""
        rate = self.tariff.rate / 100 + 1
        self.remaining_amount = round((self.amount * (rate ** (self.term))), config.DECIMAL_PLACES)
        self.monthly_payment = round((self.remaining_amount / self.term), config.DECIMAL_PLACES)

    def clean(self):
        """Perform validation checks on the investment object.

        Raises:
            ValidationError: if client is the bank
        """
        recipient_type = self.recipient_account.client.type == config.TYPE_BANK
        payment_type = self.payment_account.client.type == config.TYPE_BANK
        if recipient_type or payment_type:
            raise ValidationError(config.BANK_INVEST_ERROR)

    def save(self, *args, **kwargs):
        """Override the save method to calculate remaining amount and perform validation.

        Args:
            args (_type_): some argument.
            kwargs (_type_): some keyword.
        """
        if not self.remaining_amount:
            self.calculate_debt()
        self.full_clean()
        super().save(*args, **kwargs)

    def need_repay(self):
        """Check if the investment needs to be repaid based on the term and modification date.

        Returns:
            bool: True if the investment needs to be repaid, False otherwise.
        """
        distinction = timezone.now() - self.modified
        return distinction.days >= self.term * 365

    class Meta:
        db_table = 'investment'


account_types = (
    ('Deposit', 'Deposit'),
    ('Saving', 'Saving'),
    ('Current', 'Current'),
)


class TariffAccount(UUIDMixin, CreatedMixin, ModifiedMixin):
    """Model representing a tariff for an account.

    Attributes:
        type (models.CharField): CharField representing the type of account.
        rate (models.DecimalField): DecimalField representing the tariff rate.
    """

    type = models.CharField(
        choices=account_types,
        blank=True,
        null=False,
        max_length=config.MAX_STATUS_TYPE_LENGTH
    )
    rate = models.DecimalField(
        max_digits=config.MAX_TARIFF_DIGITS,
        decimal_places=config.DECIMAL_PLACES,
        blank=True,
        null=True,
        validators=[
            MinValueValidator(config.MIN_TARIFF_VALUE),
            MaxValueValidator(config.MAX_TARIFF_VALUE)
        ]
    )

    def save(self, *args, **kwargs):
        """Override the save method to update the modified field.

        Args:
            args (_type_): some argument.
            kwargs (_type_): some keyword.
        """
        self.modified = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """Return a string representation of the tariff."""
        return '{0} | {1}%'.format(self.type, self.rate)

    class Meta:
        db_table = 'tariff_account'


credit_types = (
    ('Auto', 'Auto'),
    ('Student', 'Student'),
    ('Home', 'Home'),
    ('Personal', 'Personal'),
    ('Business', 'Business')
)


class TariffCredit(UUIDMixin, CreatedMixin, ModifiedMixin):
    """Model representing a tariff for a credit.

    Attributes:
        type (models.CharField): CharField representing the type of credit.
        rate (models.DecimalField): DecimalField representing the tariff rate.
    """

    type = models.CharField(
        choices=credit_types,
        blank=True,
        null=False,
        max_length=config.MAX_STATUS_TYPE_LENGTH
    )
    rate = models.DecimalField(
        max_digits=config.MAX_TARIFF_DIGITS,
        decimal_places=config.DECIMAL_PLACES,
        blank=True,
        null=True,
        validators=[
            MinValueValidator(config.MIN_TARIFF_VALUE),
            MaxValueValidator(config.MAX_TARIFF_VALUE)
        ]
    )

    def save(self, *args, **kwargs):
        """Override the save method to update the modified field.

        Args:
            args (_type_): some argument.
            kwargs (_type_): some keyword.
        """
        self.modified = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """Return a string representation of the tariff."""
        return '{0} | {1}%'.format(self.type, self.rate)

    class Meta:
        db_table = 'tariff_credit'


invest_types = (
    ('Cryptocurrency', 'Cryptocurrency'),
    ('Stock', 'Stock')
)


class TariffInvestment(UUIDMixin, CreatedMixin, ModifiedMixin):
    """Model representing a tariff for an investment.

    Attributes:
        type (models.CharField): CharField representing the type of investment.
        rate (models.DecimalField): DecimalField representing the tariff rate.
    """

    type = models.CharField(
        choices=invest_types,
        blank=True,
        null=False,
        max_length=config.MAX_STATUS_TYPE_LENGTH
    )
    rate = models.DecimalField(
        max_digits=config.MAX_TARIFF_DIGITS,
        decimal_places=config.DECIMAL_PLACES,
        blank=True,
        null=True,
        validators=[
            MinValueValidator(config.MIN_TARIFF_VALUE),
            MaxValueValidator(config.MAX_TARIFF_VALUE)
        ]
    )

    def save(self, *args, **kwargs):
        """Override the save method to update the modified field.

        Args:
            args (_type_): some argument.
            kwargs (_type_): some keyword.
        """
        self.modified = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """Return a string representation of the tariff."""
        return '{0} | {1}%'.format(self.type, self.rate)

    class Meta:
        db_table = 'tariff_investment'


transact_types = (
    ('Transfer', 'Transfer'),
    ('Credit', 'Credit'),
    ('Investment', 'Investment'),
    ('Purchase', 'Purchase')
)


class Transact(UUIDMixin, CreatedMixin):
    """Model representing a transaction.

    Attributes:
        sender (models.ForeignKey): ForeignKey to the sender account.
        recipient (models.ForeignKey): ForeignKey to the recipient account.
        amount (models.DecimalField): DecimalField representing the transaction amount.
        type (models.CharField): CharField representing the type of transaction.
    """

    sender = models.ForeignKey(
        Account,
        models.DO_NOTHING,
        blank=True,
        null=False,
        related_name='sender'
    )
    recipient = models.ForeignKey(
        Account,
        models.DO_NOTHING,
        blank=True,
        null=False,
        related_name='recipient'
    )
    amount = models.DecimalField(
        max_digits=config.DECIMAL_MAX_DIGITS,
        decimal_places=config.DECIMAL_PLACES,
        blank=True,
        null=False,
        validators=[MinValueValidator(config.MIN_TRANSACT_VALUE)]
    )
    type = models.CharField(
        choices=transact_types,
        default=config.TYPE_PURCHASE,
        blank=True,
        null=False,
        max_length=config.MAX_STATUS_TYPE_LENGTH
    )

    def __str__(self) -> str:
        """Return a string representation of the transaction."""
        return 'From {0} to {1} | {2} | {3}'.format(
            self.sender.client, self.recipient.client, self.amount, self.created
        )

    def clean(self):
        """Checks for the same accounts.

        Raises:
            ValidationError: if accounts the same
        """
        if self.sender_id and self.recipient_id:
            if self.sender_id == self.recipient_id:
                raise ValidationError(config.THE_SAME_ACCOUNT_ERROR)

    def save(self, *args, **kwargs):
        """Override the save method to perform validation and save the transaction.

        Args:
            args (_type_): some argument.
            kwargs (_type_): some keyword.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'transact'


payment_statuses = (
    ('Cancelled', 'Cancelled'),
    ('Waiting', 'Waiting'),
    ('Confirmed', 'Confirmed')
)


class Payment(UUIDMixin, CreatedMixin):
    """Model representing a payment.

    Attributes:
        sender (models.ForeignKey): ForeignKey to the sender account.
        recipient (models.ForeignKey): ForeignKey to the recipient account.
        amount (models.DecimalField): DecimalField representing the payment amount.
        status (models.CharField): CharField representing the status of the payment.
        pay_date (models.DateTimeField): DateTimeField representing the payment date.
        type (models.CharField): CharField representing the type of payment.
        callback (models.JSONField): JSONField representing the payment callback.
    """

    sender = models.ForeignKey(
        Account,
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='sender_payment'
    )
    recipient = models.ForeignKey(
        Account,
        models.DO_NOTHING,
        blank=True,
        null=False,
        related_name='recipient_payment'
    )
    amount = models.DecimalField(
        max_digits=config.DECIMAL_MAX_DIGITS,
        decimal_places=config.DECIMAL_PLACES,
        blank=True,
        null=False,
        validators=[MinValueValidator(config.MIN_TRANSACT_VALUE)]
    )
    status = models.CharField(
        choices=payment_statuses,
        default=config.PAYMENT_WAITING,
        blank=True,
        null=False,
        max_length=config.MAX_STATUS_TYPE_LENGTH
    )
    pay_date = models.DateTimeField(default=timezone.now, null=False, blank=True)
    type = models.CharField(
        choices=transact_types,
        default=config.TYPE_PURCHASE,
        blank=True,
        null=False,
        max_length=config.MAX_STATUS_TYPE_LENGTH
    )
    callback = models.JSONField(max_length=config.MAX_CALLBACK_LENGTH, null=True, blank=True)

    def clean(self):
        """Checks for the same accounts.

        Raises:
            ValidationError: if accounts the same
        """
        if self.sender_id and self.recipient_id:
            if self.sender_id == self.recipient_id:
                raise ValidationError(config.THE_SAME_ACCOUNT_ERROR)

    def save(self, *args, **kwargs):
        """Override the save method to perform validation and save the payment.

        Args:
            args (_type_): some argument.
            kwargs (_type_): some keyword.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """Return a string representation of the payment."""
        return 'To {0} | {1} | {2}'.format(
            self.recipient.client,
            self.amount,
            self.status
        )

    class Meta:
        db_table = 'payment'
