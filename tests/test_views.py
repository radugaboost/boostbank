from django.test import TestCase
from selenium.webdriver.support.wait import WebDriverWait
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from django.urls import reverse
from rest_framework.status import HTTP_200_OK as OK
from django.contrib.auth.models import User
from django.test.client import Client
from bank_app import models, config
from django.contrib.staticfiles.testing import StaticLiveServerTestCase


def create_view_tests(url, page_name, template):
    class ViewTests(TestCase):

        def setUp(self):
            self.client = Client()
            self.user = User.objects.create_user(
                username='test',
                password='test'
            )
            self.client.login(username='test', password='test')

        def test_view_exists_at_url(self):
            """Test for view existing at url."""
            self.assertEqual(self.client.get(url).status_code, OK)

        def test_view_exists_by_name(self):
            """Test for view existing by name."""
            self.assertEqual(self.client.get(
                reverse(page_name)).status_code, OK)

        def test_view_uses_template(self):
            """Test for using template."""
            resp = self.client.get(reverse(page_name))
            self.assertEqual(resp.status_code, OK)
            self.assertTemplateUsed(resp, template)

    return ViewTests


HomepageViewTests = create_view_tests(
    '/',
    'homepage',
    'index.html'
)
RegistrViewTests = create_view_tests(
    '/register',
    'register',
    'registration.html'
)
LoginViewTests = create_view_tests(
    '/login/',
    'login',
    'login.html'
)


class ProfileTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='test',
            password='test'
        )
        self.client.login(username='test', password='test')
        self.model = models.Client.objects.create(
            user=self.user,
            phone_number='89889976512'
        )
        self.url = '/profile'
        self.page_name = 'profile'
        self.template = 'profile.html'

    def test_view_exists_at_url(self):
        """Test for view existing at url."""
        self.assertEqual(self.client.get(self.url).status_code, OK)

    def test_view_exists_by_name(self):
        """Test for view existing by name."""
        self.assertEqual(self.client.get(
            reverse(self.page_name)).status_code, OK)

    def test_view_uses_template(self):
        """Test for using template."""
        resp = self.client.get(reverse(self.page_name))
        self.assertEqual(resp.status_code, OK)
        self.assertTemplateUsed(resp, self.template)
        # self.assertTemplateUsed(resp, 'tickets/base.html')


class WebsiteFunctionsTests(StaticLiveServerTestCase):

    def setUp(self):
        self.name = 'TEST'
        self.email = 'test@example.com'
        self.password = '39YIExEkPa'
        self.number = '89184547890'
        self.credit_amount = 20000
        self.credit_term = 12
        self.investment_amount = 10000
        self.investment_term = 2
        self.transact_amount = 100
        self.payment_amount = 100
        bank = models.Client.objects.get(
            type='Bank'
        )
        self.bank_account = models.Account.objects.get(
            client=bank
        )
        client = models.Client.objects.create(
            user=User.objects.create_user(
                username='test1',
                password='test1'
            ),
            phone_number=89187654534
        )
        tariff = models.TariffAccount.objects.get(
            type='Deposit'
        )
        models.Account.objects.create(
            client=client,
            tariff=tariff,
            funds=10000
        )
        self.payment = models.Payment.objects.create(
            recipient=self.bank_account,
            amount=self.payment_amount
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = Options()
        for option in config.SELENIUM_OPTIONS:
            options.add_argument(option)
        for option in config.SELENIUM_EXPEREMENTAL_OPTIONS:
            options.add_experimental_option(*option)
        cls.selenium = webdriver.Chrome(options=options)
        cls.selenium.maximize_window()
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    @staticmethod
    def try_click(driver, by, locator):
        btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((by, locator))
        )
        driver.execute_script("arguments[0].click();", btn)

    @staticmethod
    def wait_for_element(driver, by, locator):
        return WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((by, locator))
        )

    def check_register(
        self, name: str, email: str,
        number: str, password: str
    ):
        username_input = self.selenium.find_element(By.NAME, "username")
        username_input.send_keys(name)
        first_name_input = self.selenium.find_element(By.NAME, "first_name")
        first_name_input.send_keys(name)
        last_name_input = self.selenium.find_element(By.NAME, "last_name")
        last_name_input.send_keys(name)
        email_input = self.selenium.find_element(By.NAME, "email")
        email_input.send_keys(email)
        phone_number_input = self.selenium.find_element(By.NAME, "phone_number")
        phone_number_input.send_keys(number)
        password1_input = self.selenium.find_element(By.NAME, "password1")
        password1_input.send_keys(password)
        password2_input = self.selenium.find_element(By.NAME, "password2")
        password2_input.send_keys(password)
        self.selenium.find_element(By.NAME, 'submit-btn').click()

    def check_create_account(self, for_fail=False):
        self.try_click(
            self.selenium,
            By.CSS_SELECTOR,
            '#action-submit'
        )
        self.try_click(
            self.selenium,
            By.CSS_SELECTOR,
            '.transfer-container > button:nth-child(4)'
        )
        if for_fail:
            self.try_click(
                self.selenium,
                By.CSS_SELECTOR,
                '.become-client-button'
            )
        else:
            self.try_click(
                self.selenium,
                By.CLASS_NAME,
                'link'
            )

    def check_create_credit(self, for_fail: bool = False):
        self.selenium.find_element(
            By.CSS_SELECTOR,
            "#choice > option:nth-child(2)"
        ).click()
        self.try_click(
            self.selenium,
            By.CSS_SELECTOR,
            '#action-submit'
        )
        amount_input = self.wait_for_element(
            self.selenium,
            By.NAME,
            'amount'
        )
        amount_input.send_keys(self.credit_amount)
        term_input = self.wait_for_element(
            self.selenium,
            By.NAME,
            'term'
        )
        term_input.send_keys(self.credit_term)
        self.try_click(
            self.selenium,
            By.NAME,
            'create-submit'
        )
        if for_fail:
            self.try_click(
                self.selenium,
                By.CSS_SELECTOR,
                '.become-client-button'
            )
        else:
            self.try_click(
                self.selenium,
                By.CLASS_NAME,
                'link'
            )

    def check_create_investment(
        self,
        amount: int,
        term: int,
        for_fail: bool = False
    ):
        self.selenium.find_element(
            By.CSS_SELECTOR,
            "#choice > option:nth-child(3)"
        ).click()
        self.try_click(
            self.selenium,
            By.CSS_SELECTOR,
            '#action-submit'
        )
        amount_input = self.wait_for_element(
            self.selenium,
            By.NAME,
            'amount'
        )
        amount_input.send_keys(amount)
        term_input = self.wait_for_element(
            self.selenium,
            By.NAME,
            'term'
        )
        term_input.send_keys(term)
        self.try_click(
            self.selenium,
            By.NAME,
            'create-submit'
        )
        if for_fail:
            self.try_click(
                self.selenium,
                By.CSS_SELECTOR,
                '.become-client-button'
            )
        else:
            self.try_click(
                self.selenium,
                By.CLASS_NAME,
                'link'
            )

    def check_transfer_funds(self, amount: int, for_fail: bool = False):
        self.try_click(
            self.selenium,
            By.CSS_SELECTOR,
            '#action-submit'
        )
        self.selenium.find_element(
            By.CSS_SELECTOR,
            '#account_tariff > option:nth-child(2)'
        ).click()
        self.try_click(
            self.selenium,
            By.CSS_SELECTOR,
            '.transfer-container > button:nth-child(4)'
        )
        if for_fail:
            self.try_click(
                self.selenium,
                By.CSS_SELECTOR,
                '.become-client-button'
            )
        else:
            self.try_click(
                self.selenium,
                By.CLASS_NAME,
                'link'
            )
        self.acc_id = self.selenium.find_element(
            By.CSS_SELECTOR,
            'div.account-row:nth-child(3) > div:nth-child(1)'
        ).get_attribute('data-account-id')
        self.selenium.find_element(
            By.CSS_SELECTOR,
            "#choice > option:nth-child(4)"
        ).click()
        self.try_click(
            self.selenium,
            By.CSS_SELECTOR,
            '#action-submit'
        )
        if for_fail:
            self.selenium.find_element(
                By.CSS_SELECTOR,
                '#sender_account > option:nth-child(2)'
            ).click()
        else:
            self.selenium.find_element(
                By.CSS_SELECTOR,
                '#sender_account > option:nth-child(1)'
            ).click()
        id_input = self.wait_for_element(
            self.selenium,
            By.CSS_SELECTOR,
            '#recipient_account'
        )
        id_input.send_keys(self.acc_id)
        amount_input = self.wait_for_element(
            self.selenium,
            By.CSS_SELECTOR,
            '#amount'
        )
        amount_input.send_keys(amount)
        self.try_click(
            self.selenium,
            By.CSS_SELECTOR,
            '.transfer-container > button:nth-child(8)'
        )
        if for_fail:
            self.try_click(
                self.selenium,
                By.CSS_SELECTOR,
                '.become-client-button'
            )
        else:
            self.try_click(
                self.selenium,
                By.CLASS_NAME,
                'link'
            )

    def check_payment(self):
        sender_account = models.Account.objects.get(
            id=self.acc_id
        )
        models.Payment.objects.create(
            sender=sender_account,
            recipient=self.bank_account,
            amount=self.payment_amount,
            type=config.TYPE_CREDIT,
            callback={
                'url': 'https://greenatom.ru/',
                'headers': 'user-agent=Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0',
                'redirect': 'https://greenatom.ru/'
            }
        )
        self.selenium.refresh()
        self.try_click(
            self.selenium,
            By.CSS_SELECTOR,
            '.payment-actions > button:nth-child(1)'
        )

    def test_profile_view(self):
        self.selenium.get(f"{self.live_server_url}/register")
        self.check_register(
            name=self.name,
            email=self.email,
            number='789',
            password=self.password
        )  # FOR FAIL
        self.check_register(
            name=self.name,
            email=self.email,
            number=self.number,
            password=self.password
        )
        self.check_create_account()
        self.check_create_account(for_fail=True)
        for _ in range(config.MAX_NUMBER_OF_CREDITS):
            self.check_create_credit()
        self.check_create_credit(for_fail=True)
        self.check_create_investment(
            amount=self.investment_amount,
            term=self.investment_term
        )
        self.check_create_investment(
            amount=10000000000,
            term=1222,
            for_fail=True
        )
        self.check_transfer_funds(amount=self.transact_amount)
        self.check_transfer_funds(amount=1200000, for_fail=True)
        self.check_transfer_funds(amount=self.transact_amount, for_fail=True)
        self.check_payment()
        self.selenium.refresh()
        self.try_click(
            self.selenium,
            By.CSS_SELECTOR,
            '.info-box > div:nth-child(5) > form:nth-child(1) > button:nth-child(2)'
        )

    def test_payment_view(self):
        self.selenium.get(f"{self.live_server_url}/payment/{self.payment.id}")
        self.try_click(
            self.selenium,
            By.CSS_SELECTOR,
            '.become-client-button'
        )
        self.check_login('test2', 'test2', for_payment=True)  # FOR FAIL
        self.check_login('test1', 'test1', for_payment=True)
        self.try_click(
            self.selenium,
            By.CSS_SELECTOR,
            '#pay-button'
        )

    def check_login(self, username: str, password: str, for_payment: bool = False):
        username_input = self.wait_for_element(
            self.selenium,
            By.CSS_SELECTOR,
            '#username'
        )
        username_input.send_keys(username)
        password_input = self.wait_for_element(
            self.selenium,
            By.CSS_SELECTOR,
            '#password'
        )
        password_input.send_keys(password)
        if for_payment:
            self.try_click(
                self.selenium,
                By.CSS_SELECTOR,
                '#pay-button'
            )
        else:
            self.try_click(
                self.selenium,
                By.CSS_SELECTOR,
                '.registration-container > form:nth-child(1) > button:nth-child(4)'
            )

    def test_bank_account(self):
        self.selenium.get(f"{self.live_server_url}/login")
        self.check_login(config.ADMIN_USERNAME, '123')        # FOR FAIL
        self.check_login(config.ADMIN_USERNAME, config.ADMIN_PASSWORD)
        self.check_create_credit(for_fail=True)
        self.check_create_investment(
            amount=self.investment_amount,
            term=self.investment_term,
            for_fail=True
        )
