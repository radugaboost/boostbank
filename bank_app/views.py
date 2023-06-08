"""Views for app."""

from django.shortcuts import render, redirect
from rest_framework import permissions, viewsets
from django.http import HttpResponseRedirect, HttpRequest
from . import config, scripts, models, serializers, forms
from django.views import View
from django.db import transaction, models as md
from django.contrib.auth.models import User
from django.contrib.auth import decorators as auth_decorators, login, authenticate, logout
from django.urls import reverse
from rest_framework.serializers import ModelSerializer


def query_from_request(request: HttpRequest, cls_serializer: ModelSerializer) -> dict:
    """Create a query dictionary from the request parameters.

    Args:
        request (HttpRequest): The HTTP request object.
        cls_serializer (ModelSerializer): The serializer class.

    Returns:
        dict: The query dictionary.

    """
    query = {}
    for attr in cls_serializer.Meta.fields:
        attr_value = request.GET.get(attr, '')
        if attr_value:
            query[attr] = attr_value
    return query


def create_viewset(
    cls_model: models.models.Model,
    serializer: ModelSerializer,
    permission: permissions.BasePermission,
    order_field: str
):
    """Create a custom ViewSet class for the given model.

    Args:
        cls_model (models.models.Model): The model class.
        serializer (ModelSerializer): The serializer class.
        permission (permissions.BasePermission): The permission class.
        order_field (str): The field to order the queryset.

    Returns:
        CustomViewSet: The custom ViewSet class.

    """
    class_name = "{0}ViewSet".format(cls_model.__name__)
    doc = "API endpoint that allows users to be viewed or edited for {0}".format(cls_model.__name__)
    return type(class_name, (viewsets.ModelViewSet,), {
    "__doc__": doc,
    "serializer_class": serializer,
    "queryset": cls_model.objects.all().order_by(order_field),
    "permission classes": [permission],
    "get_queryset": lambda self, *args, **kwargs: cls_model.objects.\
        filter(**query_from_request(self.request, serializer)).order_by(order_field)
    }
    )


def custom_main(request: HttpRequest):
    """View function for rendering the custom main template.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The HTTP response object containing the rendered template.

    """
    return render(
        request,
        config.TEMPLATE_MAIN
    )


def register(request: HttpRequest):
    """View function for handling user registration.

    Handles form submission for user registration.
    Creates a new User and Client object if the form is valid.
    Logs in the newly registered user and redirects to the profile page.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse or HttpResponseRedirect: The HTTP response object.

    """
    if request.method == 'POST':
        form = forms.RegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password1']

            with transaction.atomic():
                user = User.objects.create_user(
                    email=email,
                    username=username,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                user.save()
                client = models.Client.objects.create(
                    user=user,
                    phone_number=form.cleaned_data['phone_number']
                )
                client.save()
            login(request, user)
            return redirect('profile')
        return render(request, config.TEMPLATE_REG, {'form': form})

    form = forms.RegistrationForm()

    return render(request, config.TEMPLATE_REG, {'form': form})


@auth_decorators.login_required
def profile_page(request: HttpRequest):
    """View function for handling investment creation.

    Requires the user to be logged in.
    Retrieves the client associated with the logged-in user.
    Retrieves the client's accounts and investment tariffs.
    Handles form submission for creating investments.
    Renders the investment form and relevant data in the template.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The HTTP response object containing the rendered template.

    """
    user = request.user
    client = models.Client.objects.get(user=user)
    credits = models.Credit.objects.filter(client=client, status='Active')
    accounts = models.Account.objects.filter(client=client)
    transactions = models.Transact.objects.filter(
        md.Q(sender__in=accounts, recipient__in=accounts)
    ).order_by('-created')
    investments = models.Investment.objects.filter(client=client)
    account_tariffs = models.TariffAccount.objects.all()
    credit_tariffs = models.TariffCredit.objects.all()
    investment_tariffs = models.TariffInvestment.objects.all()
    payments = models.Payment.objects.filter(
        sender__in=accounts,
        status=config.PAYMENT_WAITING
    )

    messages = []
    total_payment = 0
    total_paid = 0
    total_investment_amount = 0

    total_payment = sum(payment.amount for payment in payments.filter(type=config.TYPE_CREDIT))
    for transact in transactions.filter(md.Q(sender__in=accounts) and md.Q(recipient__in=accounts)):
        if scripts.date_this_month(transact.created.date()):
            total_paid += transact.amount
    total_investment_amount = sum(investment.remaining_amount for investment in investments)

    total_values = {
        'total_payment': total_payment,
        'total_paid': total_paid,
        'total_investment_amount': total_investment_amount
    }

    if request.method == 'POST':
        form = forms.ProfilePaymentForm(request.POST)
        if form.is_valid():
            scripts.make_payment(
                form.cleaned_data['payment']
            )
        return redirect('profile')
    else:
        form = forms.ProfilePaymentForm()

    client_data = {
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'id': user.id,
        'credits': credits,
        'accounts': accounts,
        'transacts': transactions,
        'investments': investments,
        'account_tariffs': account_tariffs,
        'credit_tariffs': credit_tariffs,
        'investment_tariffs': investment_tariffs,
        'total_values': total_values,
        'payments': payments
    }

    return render(
        request,
        config.TEMPLATE_PROFILE,
        context={
            'client_data': client_data,
            'form': form,
            'messages': '; '.join(messages)
        },
    )


@auth_decorators.login_required
def credit_view(request: HttpRequest):
    """View function for handling credit creation.

    Requires the user to be logged in.
    Retrieves the client associated with the logged-in user.
    Retrieves the client's accounts and credit tariffs.
    Handles form submission for creating credits.
    Renders the credit form and relevant data in the template.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The HTTP response object containing the rendered template.

    """
    client = models.Client.objects.get(user_id=request.user.id)
    accounts = models.Account.objects.filter(client=client)
    credit_tariffs = models.TariffCredit.objects.all()
    messages = []

    if request.method == 'POST':
        form = forms.CreditForm(request.POST, initial={'client': client})
        if form.is_valid():
            credit = scripts.create_credit(
                client=client,
                recipient=form.cleaned_data['recipient_account'],
                payment=form.cleaned_data['payment_account'],
                amount=form.cleaned_data['amount'],
                tariff=form.cleaned_data['credit_tariff'],
                term=form.cleaned_data['term']
            )
            messages = [
                config.MESSAGE_SUCCESS.format(item='Credit'),
                config.MESSAGE_REMAINING_AMOUNT.format(value=credit.remaining_amount),
                config.MESSAGE_MONTHLY_PAYMENT.format(value=credit.monthly_payment)
            ]

    else:
        form = forms.CreditForm(initial={'client': client})

    context = {
        'accounts': accounts,
        'tariffs': credit_tariffs,
        'form': form,
        'messages': messages
    }

    return render(request, config.TEMPLATE_CREDIT, context=context)


@auth_decorators.login_required
def investment_view(request: HttpRequest):
    """View function for handling investment creation.

    Requires the user to be logged in.
    Retrieves the client associated with the logged-in user.
    Retrieves the client's accounts and investment tariffs.
    Handles form submission for creating investments.
    Renders the investment form and relevant data in the template.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The HTTP response object containing the rendered template.

    """
    client = models.Client.objects.get(user_id=request.user.id)
    accounts = models.Account.objects.filter(client=client)
    invest_tariffs = models.TariffInvestment.objects.all()
    messages = []

    if request.method == 'POST':
        form = forms.InvestmentForm(request.POST, initial={'client': client})
        if form.is_valid():
            investment = scripts.create_investment(
                client=client,
                amount=form.cleaned_data['amount'],
                recipient=form.cleaned_data['recipient_account'],
                payment=form.cleaned_data['payment_account'],
                term=form.cleaned_data['term'],
                tariff=form.cleaned_data['invest_tariff']
            )
            messages = [
                config.MESSAGE_SUCCESS.format(item='Investment'),
                config.MESSAGE_REMAINING_AMOUNT.format(value=investment.remaining_amount)
            ]
    else:
        form = forms.InvestmentForm(initial={'client': client})

    context = {
        'accounts': accounts,
        'tariffs': invest_tariffs,
        'form': form,
        'messages': messages
    }

    return render(request, config.TEMPLATE_INVESTMENT, context=context)


@auth_decorators.login_required
def transfer_view(request: HttpRequest):
    """View function for handling fund transfer.

    Requires the user to be logged in.
    Retrieves the client associated with the logged-in user.
    Retrieves the client's accounts.
    Handles form submission for fund transfer.
    Renders the transfer form and relevant data in the template.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The HTTP response object containing the rendered template.

    """
    user = request.user
    client = models.Client.objects.get(user=user)
    accounts = models.Account.objects.filter(client=client)
    messages = []

    if request.method == 'POST':
        form = forms.TransferFundsForm(request.POST, initial={'client': client})
        if form.is_valid():
            scripts.create_transact(
                sender=form.cleaned_data['sender_account'],
                recipient=form.cleaned_data['recipient_account'],
                amount=form.cleaned_data['amount'],
                transact_type=config.TYPE_TRANSFER
            )
            messages.append(config.TRANSFER_SUCCESS)
    else:
        form = forms.TransferFundsForm(initial={'client': client})

    context = {
        'accounts': accounts,
        'form': form,
        'messages': '; '.join(messages),
    }

    return render(request, config.TEMPLATE_TRANSFER, context=context)


@auth_decorators.login_required
def account_view(request: HttpRequest):
    """View function for handling account creation.

    Requires the user to be logged in.
    Retrieves the client associated with the logged-in user.
    Retrieves the available account tariffs.
    Handles form submission for creating accounts.
    Renders the account form and relevant data in the template.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The HTTP response object containing the rendered template.

    """
    client = models.Client.objects.get(user_id=request.user.id)
    tariffs = models.TariffAccount.objects.all()
    messages = []
    initial = {'client': client}

    if request.method == 'POST':
        form = forms.TariffAccountForm(request.POST, initial=initial)
        if form.is_valid():
            with transaction.atomic():
                account = models.Account.objects.create(
                    tariff=form.cleaned_data['account_tariff'],
                    client=client
                )
                account.save()
            messages.append(config.MESSAGE_SUCCESS.format(item='Account'))
    else:
        form = forms.TariffAccountForm(initial=initial)

    context = {
        'tariffs': tariffs,
        'form': form,
        'messages': '; '.join(messages)
    }

    return render(request, config.TEMPLATE_ACCOUNT, context=context)


def payment_view(request: HttpRequest, payment_id):
    """View function for handling payment processing.

    Retrieves the payment object with the given payment_id.
    Retrieves the client's accounts if the user is authenticated.
    Handles form submission for making payments.
    Renders the payment form and relevant data in the template.

    Args:
        request (HttpRequest): The HTTP request object.
        payment_id (UUID): The ID of the payment.

    Returns:
        HttpResponse: The HTTP response object containing the rendered template.

    """
    payment = models.Payment.objects.get(id=payment_id)
    accounts = None
    form = None

    if request.user.is_authenticated:
        client = models.Client.objects.get(user=request.user)
        accounts = models.Account.objects.filter(client=client)

        if request.method == 'POST':
            form = forms.PaymentForm(request.POST, initial={'payment': payment, 'client': client})
            if form.is_valid():
                with transaction.atomic():
                    payment.sender = form.cleaned_data['sender_account']
                    payment.save()
                scripts.make_payment(
                    payment
                )
        else:
            form = forms.PaymentForm(initial={'payment': payment, 'client': client})

    context = {
        'payment': payment,
        'form': form,
        'accounts': accounts,
    }

    return render(request, config.TEMPLATE_PAYMENT, context=context)


def login_page(request):
    """View function for handling user login.

    Handles form submission for user login.
    Authenticates the user and logs them in if the credentials are valid.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The HTTP response object containing the rendered template.

    """
    form_errors = []

    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password')
        )
        if user:
            login(request, user)
            return redirect('profile')
        else:
            form_errors.append(config.ERROR_LOGIN)

    return render(request, config.TEMPLATE_LOGIN, {'form_errors': '; '.join(form_errors)})


def payment_login(request, payment_id):
    """View function for handling payment login.

    Authenticates the user with the provided credentials.
    If authentication is successful, logs in the user and redirects to the payment view.
    If authentication fails, adds an error message to the form_errors list.
    Renders the payment login form with the form_errors.

    Args:
        request (HttpRequest): The HTTP request object.
        payment_id (uuid): The UUID of the payment.

    Returns:
        HttpResponse: The HTTP response object containing the rendered template.

    """
    form_errors = []

    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password')
        )
        if user:
            login(request, user)
            return redirect('/payment/{0}'.format(payment_id))
        else:
            form_errors.append(config.ERROR_LOGIN)
    return render(request, config.TEMPLATE_PAYMENT_LOGIN, {'form_errors': '; '.join(form_errors)})


@auth_decorators.login_required
def log_out(request):
    """View function for handling user logout.

    Logs out the authenticated user and redirects to the homepage.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponseRedirect: The HTTP response redirecting to the homepage.

    """
    logout(request)
    return HttpResponseRedirect(reverse('homepage'))


class RedirectPageView(View):
    """View class for redirect in main page.

    Args:
        View (_type_): _description_
    """

    def post(self, request):
        """View function for handling form submission on the redirect page.

        Retrieves the choice selected by the user and redirects to the corresponding page.

        Args:
            request (HttpRequest): The HTTP request object.

        Returns:
            HttpResponseRedirect: The HTTP response redirecting to the chosen page.

        """
        choice = request.POST.get('choice')
        if choice == 'credit':
            return redirect('credit')
        elif choice == 'transfer':
            return redirect('transfer')
        elif choice == 'account':
            return redirect('account')
        return redirect('investment')


ClientViewSet = create_viewset(
    models.Client,
    serializers.ClientSerializer,
    permissions.BasePermission,
    'user'
)
CreditViewSet = create_viewset(
    models.Credit,
    serializers.CreditSerializer,
    permissions.BasePermission,
    'id'
)
AccountViewSet = create_viewset(
    models.Account,
    serializers.AccountSerializer,
    permissions.BasePermission,
    'id'
)
TariffAccountViewSet = create_viewset(
    models.TariffAccount,
    serializers.TariffAccountSerializer,
    permissions.BasePermission,
    'id'
)
InvestmentViewSet = create_viewset(
    models.Investment,
    serializers.InvestmentSerializer,
    permissions.BasePermission,
    'id'
)
TransactViewSet = create_viewset(
    models.Transact,
    serializers.TransactSerializer,
    permissions.BasePermission,
    'id'
)
TariffInvestmentViewSet = create_viewset(
    models.TariffInvestment,
    serializers.TariffInvestmentSerializer,
    permissions.BasePermission,
    'id'
)
TariffCreditViewSet = create_viewset(
    models.TariffCredit,
    serializers.TariffCreditSerializer,
    permissions.BasePermission,
    'id'
)
PaymentViewSet = create_viewset(
    models.Payment,
    serializers.PaymentSerializer,
    permissions.BasePermission,
    'id'
)
CreditPaymentHistoryViewSet = create_viewset(
    models.CreditPaymentHistory,
    serializers.CreditPaymentHistorySerializer,
    permissions.BasePermission,
    'id'
)
