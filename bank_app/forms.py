"""Data validation forms."""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from . import models, scripts, config


class RegistrationForm(UserCreationForm):
    """Form for user registration.

    This form extends the UserCreationForm provided by Django and adds additional fields for first name,
    last name, email, phone number, and password confirmation.

    Args:
        UserCreationForm (object): Django's standard user creation form.
    """

    first_name = forms.CharField(max_length=config.CHARS_DEFAULT, required=True)
    last_name = forms.CharField(max_length=config.CHARS_DEFAULT, required=True)
    email = forms.EmailField(max_length=config.EMAIL_DEFAULT_LEN, required=True)
    phone_number = forms.CharField(
        validators=[
            models.phone_regex
        ],
        max_length=config.MAX_PHONE_LENGTH,
        required=True
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(),
        max_length=config.MAX_PASSWORD_LENGTH,
        required=True
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(),
        max_length=config.MAX_PASSWORD_LENGTH,
        required=True
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']


class ProfilePaymentForm(forms.Form):
    """Form for processing profile payments.

    This form includes a single field for the payment ID. It performs validation to check if the payment exists
    and if the sender has sufficient funds.

    Attributes:
        payment (forms.UUIDField): Field for the payment ID.

    Raises:
        ValidationError: If the payment does not exist or if the sender has insufficient funds.

    """

    payment = forms.UUIDField(label='Payment', required=True)

    def clean_payment(self):
        """Validates the payment field.

        Returns:
            Payment: The validated payment object.

        Raises:
            ValidationError: If the payment does not exist or if the sender has insufficient funds.

        """
        payment = scripts.model_exists(models.Payment, 'id', self.cleaned_data['payment'])
        if not payment:
            raise forms.ValidationError(config.NO_SUCH_PAYMENT)
        if payment.sender.funds < payment.amount:
            raise forms.ValidationError(config.INSUFFIENCIENT_FUNDS)

        return payment

    class Meta:
        model = models.Payment
        fields = ['id']


class TariffAccountForm(forms.Form):
    """Form for selecting a tariff for an account.

    This form includes a choice field for selecting the account tariff. It performs validation to check if the selected
    tariff exists and if the account already has a tariff assigned to it.

    Attributes:
        account_tariff (forms.ChoiceField): Choice field for selecting the account tariff.
        client: The client associated with the form.

    Raises:
        ValidationError: If the selected tariff does not exist or if the account already has a tariff assigned.

    """

    account_tariff = forms.ChoiceField(choices=models.account_types, required=True)

    def __init__(self, *args, **kwargs):
        """Init for TariffAccountForm.

        Args:
            args (_type_): some argument.
            kwargs (_type_): some keyword.

        """
        self.client = kwargs['initial']['client']
        super().__init__(*args, **kwargs)

    def clean_account_tariff(self):
        """Validates the account_tariff field.

        Returns:
            str: The validated account tariff.

        Raises:
            ValidationError: If the selected tariff does not exist
                or if the account already has a tariff assigned.

        """
        account_tariff = scripts.model_exists(
            models.TariffAccount,
            'type',
            self.cleaned_data['account_tariff']
        )
        if not account_tariff:
            raise forms.ValidationError(config.NO_SUCH_TARIFF)
        if models.Account.objects.filter(client=self.client, tariff=account_tariff).exists():
            raise forms.ValidationError(config.ACCOUNT_TARIFF_EXISTS)

        return account_tariff

    class Meta:
        model = models.TariffAccount
        fields = ['tariff']


class InvestmentForm(forms.Form):
    """Form for creating an investment.

    This form includes fields for specifying the investment amount,
    recipient account, payment account, investment term,
    and investment tariff. It performs validation to check
    if the specified investment tariff exists and if the provided
    accounts are valid and owned by the client. It also checks
    if the payment account has sufficient funds for the
    investment amount.

    Attributes:
        amount (forms.DecimalField): Field for specifying the investment amount.
        recipient_account (forms.UUIDField): Field for specifying the recipient account.
        payment_account (forms.UUIDField): Field for specifying the payment account.
        term (forms.IntegerField): Field for specifying the investment term.
        invest_tariff (forms.ChoiceField): Choice field for selecting the investment tariff.
        client: The client associated with the form.

    Raises:
        ValidationError: If the specified investment tariff does not exist, if the provided accounts are invalid
            or not owned by the client, or if the payment account has insufficient funds.

    """

    amount = forms.DecimalField(
        label='Amount',
        max_digits=config.DECIMAL_MAX_DIGITS,
        decimal_places=config.DECIMAL_PLACES,
        min_value=config.MIN_INVESTMENT_VALUE,
        max_value=config.MAX_INVESTMENT_VALUE,
        required=True
    )
    recipient_account = forms.UUIDField(label='Recipient account', required=True)
    payment_account = forms.UUIDField(label='Payment account', required=True)
    term = forms.IntegerField(
        validators=[
            MinValueValidator(config.MIN_INVESTMENT_TERM),
            MaxValueValidator(config.MAX_INVESTMENT_TERM)
        ],
        required=True
    )
    invest_tariff = forms.ChoiceField(choices=models.invest_types, required=True)

    def __init__(self, *args, **kwargs):
        """Init for InvestmentForm.

        Args:
            args (_type_): some argument.
            kwargs (_type_): some keyword.

        """
        self.client = kwargs['initial']['client']
        super().__init__(*args, **kwargs)

    def clean_invest_tariff(self):
        """Validates the invest_tariff field.

        Returns:
            str: The validated investment tariff.

        Raises:
            ValidationError: If the specified investment tariff does not exist.

        """
        invest_tariff = scripts.model_exists(
            models.TariffInvestment,
            'type',
            self.cleaned_data['invest_tariff']
        )

        if not invest_tariff:
            raise forms.ValidationError(config.NO_SUCH_TARIFF)

        if models.Investment.objects.filter(client=self.client, tariff=invest_tariff).exists():
            raise forms.ValidationError(config.INVESTMENT_TARIFF_EXISTS)

        return invest_tariff

    def clean_account(self, account_field):
        """Validates the recipient_account and payment_account fields.

        Args:
            account_field (str): The field name of the account to validate.

        Returns:
            Account: The validated account.

        Raises:
            ValidationError: If the specified account does not exist,
                if the account is not owned by the client,
                if the account is of type "Bank", or if the payment account has insufficient funds.

        """
        account = scripts.model_exists(
            model=models.Account,
            field_name='id',
            field_value=self.cleaned_data[account_field],
        )

        if not account:
            raise forms.ValidationError(config.NO_ACCOUNT)

        if account.client != self.client:
            raise forms.ValidationError(config.ACCOUNT_OWNER_ERROR)

        if account.client.type == config.TYPE_BANK:
            raise forms.ValidationError(config.BANK_CREDIT_ERROR)

        if account_field == 'payment_account':
            if self.cleaned_data.get('amount'):
                if account.funds < self.cleaned_data['amount']:
                    raise forms.ValidationError(config.INSUFFIENCIENT_FUNDS)

        return account

    def clean_recipient_account(self):
        """Validates the recipient_account field.

        Returns:
            Account: The validated recipient account.

        """
        return self.clean_account('recipient_account')

    def clean_payment_account(self):
        """Validates the payment_account field.

        Returns:
            Account: The validated payment account.

        """
        return self.clean_account('payment_account')

    class Meta:
        model = models.Investment
        fields = ['amount', 'term', 'recipient_account', 'payment_account', 'tariff']


class CreditForm(forms.Form):
    """Form for creating a credit.

    This form includes fields for specifying the credit amount, recipient account,
    payment account, credit term,
    and credit tariff. It performs validation to check
    if the specified credit tariff exists, if the provided
    accounts are valid and owned by the client,
    if the bank has solvency for the credit amount, and if the client
    has reached the maximum number of credits.

    Attributes:
        amount (forms.DecimalField): Field for specifying the credit amount.
        recipient_account (forms.UUIDField): Field for specifying the recipient account.
        payment_account (forms.UUIDField): Field for specifying the payment account.
        term (forms.IntegerField): Field for specifying the credit term.
        credit_tariff (forms.ChoiceField): Choice field for selecting the credit tariff.
        client: The client associated with the form.

    Raises:
        forms.ValidationError: If the specified credit tariff does not exist, if the provided accounts are invalid
            or not owned by the client, if the bank does not have solvency for the credit amount, or if the client
            has reached the maximum number of credits.

    """

    amount = forms.DecimalField(
        label='Amount',
        max_digits=config.DECIMAL_MAX_DIGITS,
        max_value=config.MAX_CREDIT_VALUE,
        min_value=config.MIN_CREDIT_VALUE,
        decimal_places=config.DECIMAL_PLACES,
        required=True
    )
    recipient_account = forms.UUIDField(label='Recipient account', required=True)
    payment_account = forms.UUIDField(label='Payment account', required=True)
    term = forms.IntegerField(
        validators=[
            MinValueValidator(config.MIN_CREDIT_TERM),
            MaxValueValidator(config.MAX_CREDIT_TERM)
        ],
        required=True
    )
    credit_tariff = forms.ChoiceField(choices=models.credit_types, required=True)

    def __init__(self, *args, **kwargs):
        """Init for CreditForm.

        Args:
            args (_type_): some argument.
            kwargs (_type_): some keyword.

        """
        self.client = kwargs['initial']['client']
        super().__init__(*args, **kwargs)

    def clean(self):
        """Performs form-wide validation.

        Returns:
            dict: The cleaned form data.

        Raises:
            ValidationError: If the client has reached the maximum number of credits.

        """
        cleaned_data = super().clean()
        if models.Credit.objects.filter(client=self.client).count() == config.MAX_NUMBER_OF_CREDITS:
            raise forms.ValidationError(config.MAX_NUMBER_CREDITS_ERROR)
        return cleaned_data

    def clean_amount(self):
        """Validates the amount field.

        Returns:
            Decimal: The validated credit amount.

        Raises:
            ValidationError: If the bank does not have solvency for the credit amount.

        """
        if not scripts.bank_solvency_check(self.cleaned_data['amount']):
            raise forms.ValidationError(config.NOT_SOLVENCY_BANK)
        return self.cleaned_data['amount']

    def clean_credit_tariff(self):
        """Validates the credit_tariff field.

        Returns:
            str: The validated credit tariff.

        Raises:
            ValidationError: If the specified credit tariff does not exist.

        """
        credit_tariff = scripts.model_exists(
            models.TariffCredit,
            'type',
            self.cleaned_data['credit_tariff']
        )
        if not credit_tariff:
            raise forms.ValidationError(config.NO_SUCH_TARIFF)
        return credit_tariff

    def clean_account(self, account_field):
        """Validates the recipient_account and payment_account fields.

        Args:
            account_field (str): The field name of the account to validate.

        Returns:
            Account: The validated account.

        Raises:
            ValidationError: If the specified account does not exist, if the account is not owned by the client,
                if the account type is "bank", or if the payment account has insufficient funds.

        """
        account = scripts.model_exists(
            model=models.Account,
            field_name='id',
            field_value=self.cleaned_data[account_field],
        )

        if not account:
            raise forms.ValidationError(config.NO_ACCOUNT)

        if account.client != self.client:
            raise forms.ValidationError(config.ACCOUNT_OWNER_ERROR)

        if account.client.type == config.TYPE_BANK:
            raise forms.ValidationError(config.BANK_CREDIT_ERROR)

        return account

    def clean_recipient_account(self):
        """Validates the recipient_account field.

        Returns:
            Account: The validated recipient account.

        """
        return self.clean_account('recipient_account')

    def clean_payment_account(self):
        """Validates the payment_account field.

        Returns:
            Account: The validated payment account.

        """
        return self.clean_account('payment_account')

    class Meta:
        model = models.Credit
        fields = ['amount', 'term', 'recipient_account', 'payment_account', 'tariff']


class PaymentForm(forms.Form):
    """Form for making a payment.

    This form includes a field for specifying the sender account. It performs validation to check if the specified
    sender account exists, is owned by the client, and has sufficient funds for the payment.

    Attributes:
        sender_account (forms.UUIDField): Field for specifying the sender account.
        payment: The payment associated with the form.
        client: The client associated with the form.

    Raises:
        forms.ValidationError: If the specified sender account does not exist, is not owned by the client, or does not
            have sufficient funds for the payment.

    """

    sender_account = forms.UUIDField(label='Payment account', required=True)

    def __init__(self, *args, **kwargs):
        """Init for PaymentForm.

        Args:
            args (_type_): some argument.
            kwargs (_type_): some keyword.

        """
        self.payment = kwargs['initial']['payment']
        self.client = kwargs['initial']['client']
        super().__init__(*args, **kwargs)

    def clean_sender_account(self):
        """Validates the sender_account field.

        Returns:
            Account: The validated sender account.

        Raises:
            ValidationError: If the specified sender account does not exist, is not owned by the client, or does
                not have sufficient funds for the payment.

        """
        sender_account = scripts.model_exists(
            model=models.Account,
            field_name='id',
            field_value=self.cleaned_data['sender_account'],
        )
        if not sender_account:
            raise forms.ValidationError(config.NO_ACCOUNT)

        if sender_account.client != self.client:
            raise forms.ValidationError(config.ACCOUNT_OWNER_ERROR)

        if sender_account.funds < self.payment.amount:
            raise forms.ValidationError(config.INSUFFIENCIENT_FUNDS)

        return sender_account

    class Meta:
        model = models.Account
        fields = ['id']


class TransferFundsForm(forms.Form):
    """Form for transferring funds between accounts.

    This form includes fields for specifying the amount, recipient account,
    and sender account. It performs validations
    to ensure that the sender and recipient accounts exist,
    are owned by the client (sender account), and have
    sufficient funds (sender account) for the transfer.

    Attributes:
        amount (forms.DecimalField): Field for specifying the amount to transfer.
        recipient_account (forms.UUIDField): Field for specifying the recipient account.
        sender_account (forms.UUIDField): Field for specifying the sender account.
        client: The client associated with the form.

    Raises:
        ValidationError: If the sender and recipient accounts are the same,
            if either account does not exist,
            if the sender account is not owned by the client,
            or if the sender account does not have sufficient funds.

    """

    amount = forms.DecimalField(
        label='Amount',
        max_digits=config.DECIMAL_MAX_DIGITS,
        decimal_places=config.DECIMAL_PLACES,
        required=True,
        min_value=config.MIN_TRANSACT_VALUE
    )
    recipient_account = forms.UUIDField(label='Recipient account', required=True)
    sender_account = forms.UUIDField(label='Payment account', required=True)

    def __init__(self, *args, **kwargs):
        """Init for TransferFundsForm.

        Args:
            args (_type_): some argument.
            kwargs (_type_): some keyword.

        """
        self.client = kwargs['initial']['client']
        super().__init__(*args, **kwargs)

    def clean(self):
        """Performs additional form-level validation.

        Raises:
            ValidationError: If the sender and recipient accounts are the same.

        """
        cleaned_data = super().clean()
        sender_account = cleaned_data.get('sender_account')
        recipient_account = cleaned_data.get('recipient_account')

        if sender_account == recipient_account:
            raise forms.ValidationError(config.THE_SAME_ACCOUNT_ERROR)

    def clean_account(self, account_field):
        """Validates the sender_account and recipient_account fields.

        Args:
            account_field (str): The name of the account field to validate.

        Raises:
            ValidationError: If the specified account does not exist.
            ValidationError: If the client not account owner.
            ValidationError: If there are not enough funds on the account.

        Returns:
            Account: The validated account.
        """
        account = scripts.model_exists(
            model=models.Account,
            field_name='id',
            field_value=self.cleaned_data[account_field],
        )

        if not account:
            raise forms.ValidationError(config.NO_ACCOUNT)

        if account_field == 'sender_account':
            if account.client != self.client:
                raise forms.ValidationError(config.ACCOUNT_OWNER_ERROR)

            if self.cleaned_data.get('amount'):
                if account.funds < self.cleaned_data.get('amount'):
                    raise forms.ValidationError(config.INSUFFIENCIENT_FUNDS)

        return account

    def clean_recipient_account(self):
        """Validates the recipient_account field.

        Returns:
            Account: The validated recipient account.

        """
        return self.clean_account('recipient_account')

    def clean_sender_account(self):
        """Validates the sender_account field.

        Returns:
            Account: The validated sender account.

        """
        return self.clean_account('sender_account')

    class Meta:
        model = models.Transact
        fields = ['amount', 'sender', 'recipient']
