import contextlib
import logging
import datetime
import requests
import time
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import SessionNotCreatedException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
import chromedriver_binary

logger = logging.getLogger('bofa')
logging.basicConfig(level=logging.INFO)

login_url = 'https://www.bankofamerica.com'
header = 'https://secure.bankofamerica.com'
verification_url = 'https://secure.bankofamerica.com/login/sign-in/signOnSuccessRedirect.go'
account_url = 'https://secure.bankofamerica.com/myaccounts/signin/signIn.go'
tags = {
    'username': 'onlineId1',
    'password': 'passcode1',
    'text': 'rbText',
    'phone': 'rbVoice',
    'continue': 'btnARContinue',
    'code': 'tlpvt-acw-authnum',
    'remember': 'yes-recognize',
    'verify': 'continue-auth-number'
}
css_sel = {
    'names': 'span[class=\'AccountName\'] a',
    'balances': 'div[class=\'AccountBalance\'] span'
}
verification_method = 'text'  # or 'phone'


class Scraper:
    def __init__(self, credentials, start_date=None, end_date=None, **kwargs):
        self.credentials = credentials
        self.source = None
        try:
            self.start_date = process_date(start_date)
            self.end_date = process_date(end_date)
        except Exception as e:
            logger.error(e)
            return
        try:
            op = webdriver.ChromeOptions()
            # op.add_argument('headless')
            self.driver = webdriver.Chrome(options=op)
        except SessionNotCreatedException as e:
            logger.error(e)
            return
        self.logged_in = False

    def login(self):
        if self.logged_in:
            return
        logger.info('Logging in with credentials...')
        self.driver.get(login_url)
        try:
            self.driver.find_element_by_id(tags['username']).send_keys(self.credentials['username'])
            self.driver.find_element_by_id(tags['password']).send_keys(self.credentials['password'])
            try:
                with self.wait_for_page_load(timeout=10):
                    self.driver.find_element_by_id(tags['password']).send_keys(Keys.ENTER)
            except TimeoutException:
                logger.error('Timeout. Please try again')  # TODO: add retry feature
        except NoSuchElementException:
            logger.error('Missing element id: username or password')
        # verify login
        current_url = str(self.driver.current_url)
        if current_url.find(account_url) == 0:
            logger.info('Successful login')
            self.logged_in = True
        elif current_url.find(verification_url) == 0:
            logger.info('Verifying identity...')
            try:
                self.driver.find_element_by_id(tags[verification_method]).click()
                self.driver.find_element_by_id(tags['continue']).click()
                while str(self.driver.current_url).find(account_url) == -1:
                    code = input('Please enter 6-digit authorization code: ')
                    self.driver.find_element_by_id(tags['code']).send_keys(code)
                    self.driver.find_element_by_id(tags['remember']).click()
                    self.driver.find_element_by_id(tags['verify']).click()
            except NoSuchElementException:
                logger.error('Missing element id: verification method, verification code or button')
            self.logged_in = True
        else:
            logger.info('Failed login. Please check your credentials')
            self.logged_in = False
        self.source = self.driver.page_source
        self.driver.close()

    @contextlib.contextmanager
    def wait_for_page_load(self, timeout=30):
        old = self.driver.find_element_by_tag_name('html')
        yield
        WebDriverWait(self.driver, timeout).until(
            expected_conditions.staleness_of(old)
        )

    def fetch_accounts(self):
        soup = BeautifulSoup(self.source, 'html.parser')
        # print(soup.prettify())
        try:
            accounts = []
            urls = []
            for account in soup.select(css_sel['names']):
                accounts.append(account.text)
                url = str(account['href'])
                # TODO: if class name contains "AccountItem AccountItemDeposit" then direct to "deposit" info
                #       otherwise, if class name contains "AccountItem AccountItemCreditCard" then direct to "card" info
                type = 'deposit'  # or 'card'
                info_header = 'https://secure.bankofamerica.com/myaccounts/details/' + type + '/information-services.go?adx='
                idx = url.find('adx=')
                if idx != -1:
                    url = info_header + url[idx + 4:]
                else:
                    url = ''
                urls.append(url)
            balances = []
            for balance in soup.select(css_sel['balances']):
                balances.append(balance.text)
            print(accounts)
            print(balances)
            print(urls)
        except AttributeError:
            logger.error('Cannot find account items / login failed')


# process the date and return in the format of mm/dd/yyyy
def process_date(date):
    today = datetime.date.today()
    date_re = r'^\d{2}\/\d{2}\/\d{4}$'

    if date is None:
        return today
    else:
        if isinstance(date, str):
            if re.match(date_re, date):
                return date
            else:
                raise Exception('Invalid date format. Use mm/dd/yyyy')
        else:
            raise Exception('Invalid date type. Use str or int')


if __name__ == '__main__':
    username = input('Please enter username: ')
    password = input('Please enter password: ')
    cred = {'username': username, 'password': password}
    scraper = Scraper(credentials=cred)
    scraper.login()
    scraper.fetch_accounts()
