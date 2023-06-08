"""Registration models in admin panel."""

from django.contrib import admin
from . import models


class AccountInline(admin.TabularInline):
    """Inline admin configuration for displaying Account models.

    This class is used to display Account models inline within another model's admin page in a tabular format.

    Attributes:
        model (type): The Account model class to display.
        extra (int): The number of extra empty forms to display for adding new instances.

    """

    model = models.Account
    extra = 1


class CreditInline(admin.TabularInline):
    """Inline admin configuration for displaying Credit models.

    This class is used to display Credit models inline within another model's admin page in a tabular format.

    Attributes:
        model (type): The Credit model class to display.
        extra (int): The number of extra empty forms to display for adding new instances.

    """

    model = models.Credit
    extra = 1


class InvestmentInline(admin.TabularInline):
    """Inline admin configuration for displaying Investment models.

    This class is used to display Investment models inline within another model's admin page in a tabular format.

    Attributes:
        model (type): The Investment model class to display.
        extra (int): The number of extra empty forms to display for adding new instances.

    """

    model = models.Investment
    extra = 1


class SenderTransactInline(admin.TabularInline):
    """Inline admin configuration for displaying Transact models where the sender is the foreign key.

    This class is used to display Transact models inline within another model's admin page in a tabular format,
    specifically when the sender field is the foreign key.

    Attributes:
        model (type): The Transact model class to display.
        fk_name (str): The name of the foreign key field.
        extra (int): The number of extra empty forms to display for adding new instances.

    """

    model = models.Transact
    fk_name = 'sender'
    extra = 1


class RecipientTransactInline(admin.TabularInline):
    """Inline admin configuration for displaying Transact models where the recipient is the foreign key.

    This class is used to display Transact models inline within another model's admin page in a tabular format,
    specifically when the recipient field is the foreign key.

    Attributes:
        model (type): The Transact model class to display.
        fk_name (str): The name of the foreign key field.
        extra (int): The number of extra empty forms to display for adding new instances.

    """

    model = models.Transact
    fk_name = 'recipient'
    extra = 1


class RecipientPaymentInline(admin.TabularInline):
    """Inline admin configuration for displaying Payment models where the recipient is the foreign key.

    This class is used to display Payment models inline within another model's admin page in a tabular format,
    specifically when the recipient field is the foreign key.

    Attributes:
        model (type): The Payment model class to display.
        fk_name (str): The name of the foreign key field.
        extra (int): The number of extra empty forms to display for adding new instances.

    """

    model = models.Payment
    fk_name = 'recipient'
    extra = 1


class SenderPaymentInline(admin.TabularInline):
    """Inline admin configuration for displaying Payment models where the sender is the foreign key.

    This class is used to display Payment models inline within another model's admin page in a tabular format,
    specifically when the sender field is the foreign key.

    Attributes:
        model (type): The Payment model class to display.
        fk_name (str): The name of the foreign key field.
        extra (int): The number of extra empty forms to display for adding new instances.

    """

    model = models.Payment
    fk_name = 'sender'
    extra = 1


class CreditPaymentHistoryInline(admin.TabularInline):
    """Inline admin configuration for displaying CreditPaymentHistory models.

    This class is used to display CreditPaymentHistory models inline
    within another model's admin page in a tabular format.

    Attributes:
        model (type): The CreditPaymentHistory model class to display.
        extra (int): The number of extra empty forms to display for adding new instances.

    """

    model = models.CreditPaymentHistory
    extra = 1


@admin.register(models.Client)
class ClientAdmin(admin.ModelAdmin):
    """Register Client Admin Model.

    This class is used to customize the administration interface for the Client model.

    Attributes:
        inlines (list): A list of inline configurations to display related models inline.
        model (type): The Client model class.
        list_filter (tuple): The fields to use as filters in the admin list view.

    """

    inlines = [
        AccountInline,
        CreditInline,
        InvestmentInline
    ]

    model = models.Client
    list_filter = (
        'user',
    )


@admin.register(models.Account)
class AccountAdmin(admin.ModelAdmin):
    """Register Account Admin Model.

    This class is used to customize the administration interface for the Account model.

    Attributes:
        inlines (list): A list of inline configurations to display related models inline.
        model (type): The Account model class.
        list_filter (tuple): The fields to use as filters in the admin list view.

    """

    inlines = [
        SenderTransactInline,
        RecipientTransactInline,
        RecipientPaymentInline,
        SenderPaymentInline
    ]

    model = models.Account
    list_filter = (
        'client',
    )


@admin.register(models.Transact)
class TransactAdmin(admin.ModelAdmin):
    """Register Transact Admin Model.

    This class is used to customize the administration interface for the Transact model.

    Attributes:
        model (type): The Transact model class.
        list_filter (tuple): The fields to use as filters in the admin list view.

    """

    model = models.Transact
    list_filter = (
        'sender',
        'recipient'
    )


@admin.register(models.TariffAccount)
class TariffAccountAdmin(admin.ModelAdmin):
    """Register Tariff Account Admin Model.

    This class is used to customize the administration interface for the TariffAccount model.

    Attributes:
        inlines (list): The inline models to include in the admin interface.
        model (type): The TariffAccount model class.
        list_filter (tuple): The fields to use as filters in the admin list view.

    """

    inlines = [AccountInline]

    model = models.TariffAccount
    list_filter = (
        'type',
    )


@admin.register(models.TariffCredit)
class TariffCreditAdmin(admin.ModelAdmin):
    """Register Tariff Credit Admin Model.

    This class is used to customize the administration interface for the TariffCredit model.

    Attributes:
        inlines (list): The inline models to include in the admin interface.
        model (type): The TariffCredit model class.
        list_filter (tuple): The fields to use as filters in the admin list view.

    """

    inlines = [CreditInline]

    model = models.TariffCredit
    list_filter = (
        'type',
    )


@admin.register(models.TariffInvestment)
class TariffInvestmentAdmin(admin.ModelAdmin):
    """Register Tariff Investment Admin Model.

    This class is used to customize the administration interface for the TariffInvestment model.

    Attributes:
        inlines (list): The inline models to include in the admin interface.
        model (type): The TariffInvestment model class.
        list_filter (tuple): The fields to use as filters in the admin list view.

    """

    inlines = [InvestmentInline]

    model = models.TariffInvestment
    list_filter = (
        'type',
    )


@admin.register(models.Credit)
class CreditAdmin(admin.ModelAdmin):
    """Register Credit Admin Model.

    This class is used to customize the administration interface for the Credit model.

    Attributes:
        inlines (list): The inline models to include in the admin interface.
        model (type): The Credit model class.
        list_filter (tuple): The fields to use as filters in the admin list view.

    """

    inlines = [CreditPaymentHistoryInline]

    model = models.Credit
    list_filter = (
        'client',
    )


@admin.register(models.Investment)
class InvestmentAdmin(admin.ModelAdmin):
    """Register Investment Admin Model.

    This class is used to customize the administration interface for the Investment model.

    Attributes:
        model (type): The Investment model class.
        list_filter (tuple): The fields to use as filters in the admin list view.

    """

    model = models.Investment
    list_filter = (
        'client',
    )


@admin.register(models.Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Register Payment Admin Model.

    This class is used to customize the administration interface for the Payment model.

    Attributes:
        model (type): The Payment model class.
        list_filter (tuple): The fields to use as filters in the admin list view.

    """

    model = models.Payment
    list_filter = (
        'sender',
        'recipient'
    )


@admin.register(models.CreditPaymentHistory)
class CreditPaymentHistoryAdmin(admin.ModelAdmin):
    """Register CreditPaymentHistory Admin Model.

    This class is used to customize the administration interface for the CreditPaymentHistory model.

    Attributes:
        model (type): The CreditPaymentHistory model class.
        list_filter (tuple): The fields to use as filters in the admin list view.

    """

    model = models.CreditPaymentHistory
    list_filter = (
        'credit',
    )
