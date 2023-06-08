from os import getenv
from dotenv import load_dotenv

dotenv_path = './mysite/.env'

load_dotenv(dotenv_path)

SAFE_METHODS = 'GET', 'HEAD', 'PATCH'
UNSAFE_METHODS = 'POST', 'PUT', 'DELETE'

### ADMIN CREDS FROM DOTENV
ADMIN_USERNAME = getenv('ADMIN_USERNAME')
ADMIN_FIRST_NAME = getenv('ADMIN_FIRST_NAME')
ADMIN_LAST_NAME = getenv('ADMIN_LAST_NAME')
ADMIN_EMAIL = getenv('ADMIN_EMAIL')
ADMIN_PASSWORD = getenv('ADMIN_PASSWORD')
ADMIN_PHONE_NUMBER = getenv('ADMIN_PHONE_NUMBER')

INITIAL_BANK_FUNDS = 1000000000000000
MAX_CREDIT_VALUE = 10000000
MIN_CREDIT_VALUE = 1000
MAX_INVESTMENT_VALUE = 1000000
MIN_INVESTMENT_VALUE = 1000
MAX_NUMBER_OF_CREDITS = 3
MIN_CREDIT_TERM = 3 ## MONTHS
MAX_CREDIT_TERM = 120
MAX_INVESTMENT_TERM = 10 ## YEARS
MIN_INVESTMENT_TERM = 1
MIN_TRANSACT_VALUE = 1
MAX_STATUS_TYPE_LENGTH = 16
MAX_CALLBACK_LENGTH = 255
MIN_TARIFF_VALUE = 0
MAX_TARIFF_VALUE = 20
MAX_TARIFF_DIGITS = 4
MAX_PHONE_LENGTH = 11
INIT_ACCOUNT_BALANCE = 0
INIT_PERCENTAGE_INTERVAL = (1, 20) ## INTERVAL FOR TARIFFS DURING INIT

TEMPLATE_MAIN = 'index.html'
TEMPLATE_REG = 'registration.html'
TEMPLATE_PROFILE = 'profile.html'
TEMPLATE_PAYMENT = 'payment.html'
TEMPLATE_PAYMENT_LOGIN = 'payment_login.html'
TEMPLATE_LOGIN = 'login.html'
TEMPLATE_CREDIT = 'credit.html'
TEMPLATE_INVESTMENT = 'investment.html'
TEMPLATE_ACCOUNT = 'account.html'
TEMPLATE_TRANSFER = 'transfer.html'

CHARS_DEFAULT = 40
EMAIL_DEFAULT_LEN = 256


MESSAGE_SUCCESS = '{item} created successfully'
MESSAGE_REMAINING_AMOUNT = 'Remaining amount: ${value}'
MESSAGE_MONTHLY_PAYMENT = 'Monthly payment: ${value}'
TRANSFER_SUCCESS = 'Funds transfer was successful'
PAY_DATE_DAYS = 365 * 5 ## FOR PAYMNETS FROM BANK


PAYMENT_WAITING = 'Waiting'
PAYMENT_CONFIRMED = 'Confirmed'
PAYMENT_CANCELLED = 'Cancelled'
PAYMENT_MODIFY_ERROR = "Cannot modify this payment."
PAYMENT_NOT_CHANGED = [PAYMENT_CONFIRMED, PAYMENT_CANCELLED]


TYPE_TRANSFER = 'Transfer'
TYPE_PURCHASE = 'Purchase'
TYPE_CREDIT = 'Credit'
TYPE_BANK = 'Bank'
TYPE_PRIVATE = 'Private'
TYPE_INVESTMENT = 'Investment'
PAID_STATUS = 'Paid'
ACTIVE_STATUS = 'Active'


ERROR_FUNDS = 'Insufficient funds'
ERROR_LOGIN = 'Invalid username or password'
ERROR_PAYMENT = 'An error occurred with {payment}: {error}'
ERROR_ACCOUNT_NOT_EXISTS = 'No such account exists.'
NO_SUCH_TARIFF = 'No such tariff.'
NO_SUCH_PAYMENT = 'No such payment.'
INSUFFIENCIENT_FUNDS = 'Insufficient funds.'
ACCOUNT_TARIFF_EXISTS = 'You already have an account with this tariff.'
INVESTMENT_TARIFF_EXISTS = 'You already have an investment with this tariff.'
ACCOUNT_OWNER_ERROR = 'You must be the account owner.'
NO_ACCOUNT = 'Account does not exists.'
MAX_NUMBER_CREDITS_ERROR = 'You have reached the maximum number of credits.'
THE_SAME_ACCOUNT_ERROR = 'Accounts cannot be the same.'
NOT_SOLVENCY_BANK = 'The bank is unable to pay this amount.'
NO_SUCH_USER = 'No such user exists.'
WRONG_PASSWORD = 'Wrong password.'
MAX_LENGTH_USERNAME = 150

BANK_INVEST_ERROR = 'The bank cannot invest in itself.'
BANK_CREDIT_ERROR = 'The bank cannot take out a credit from itself.'
PHONE_NUMBER_ERROR = "Phone number must start with 8 and contain 11 digits."
DATE_ERROR = '{field} date cannot be in the future.'
TRANSCT_MODIFY_ERROR = "This object cannot be changed."

FILENAME_CALLBACK_ERRORS = "callback.log"

DECIMAL_PLACES = 2
DECIMAL_MAX_DIGITS = 20
MAX_PASSWORD_LENGTH = 30

SELENIUM_OPTIONS = [
    '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
    '--disable-dev-shm-usage',
    '--disable-blink-features=AutomationControlled',
    'disable-infobars',
    '--headless'
]
SELENIUM_EXPEREMENTAL_OPTIONS = [
    ("excludeSwitches", ["enable-automation"]),
    ('useAutomationExtension', False)
]
