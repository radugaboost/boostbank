"""Urls for views."""

from django.urls import path, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
# register our REST views in router object
router.register(r'credit', views.CreditViewSet)
router.register(r'investment', views.InvestmentViewSet)
router.register(r'account', views.AccountViewSet)
router.register(r'client', views.ClientViewSet)
router.register(r'tariff_account', views.TariffAccountViewSet)
router.register(r'tariff_credit', views.TariffCreditViewSet)
router.register(r'tariff_investment', views.TariffInvestmentViewSet)
router.register(r'payment', views.PaymentViewSet)
router.register(r'transact', views.TransactViewSet)
router.register(r'credit_payment_history', views.CreditPaymentHistoryViewSet)

urlpatterns = [
    path('rest/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('', views.custom_main, name='homepage'),
    path('register', views.register, name='register'),
    path('profile', views.profile_page, name='profile'),
    path('payment/<uuid:payment_id>/', views.payment_view, name='payment'),
    path('payment/<uuid:payment_id>/login/', views.payment_login, name='payment_login'),
    path('exit', views.log_out, name='exit'),
    path('login/', views.login_page, name='login'),
    path('profile/transfer', views.transfer_view, name='transfer'),
    path('profile/credit', views.credit_view, name='credit'),
    path('profile/investment', views.investment_view, name='investment'),
    path('profile/account', views.account_view, name='account'),
    path('redirect_page', views.RedirectPageView.as_view(), name='redirect_page')
]
