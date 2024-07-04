import requests
from kiteconnect import KiteConnect
import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.common.by import By
import time
import pyotp

from credentials_zerodha import USERNAME, PASSWORD, API_KEY, API_SECRET, TOTP_TOKEN
from api_urls import BASE_URL, TWOFA_URL, LOGIN_URL


class Auth:
    def __init__(self, broker="kite"):
        self.user_id = USERNAME
        self.user_pwd = PASSWORD
        self.api_key = API_KEY
        self.api_secret = API_SECRET
        self.session = requests.Session()

        if broker == "kite":
            self.user_id = USERNAME
            self.user_pwd = PASSWORD
            self.api_key = API_KEY
            self.api_secret = API_SECRET
            self.totp_key = TOTP_TOKEN

    def login(self, mfa_key=""):
        print("api_key: ", self.api_key)
        driver = uc.Chrome()
        driver.get(f'https://kite.trade/connect/login?api_key={self.api_key}&v=3')
        login_id = WebDriverWait(driver, 10).until(lambda x: x.find_element("xpath", '//*[@id="userid"]'))
        login_id.send_keys(self.user_id)

        pwd = WebDriverWait(driver, 10).until(lambda x: x.find_element("xpath", '//*[@id="password"]'))
        pwd.send_keys(self.user_pwd)

        submit = WebDriverWait(driver, 10).until(
            lambda x: x.find_element("xpath", '//*[@id="container"]/div/div/div[2]/form/div[4]/button'))
        submit.click()

        time.sleep(1)
        # adjustment to code to include totp
        totp = WebDriverWait(driver, 10).until(lambda x: x.find_element("xpath", '//*[@id="userid"]'))
        if mfa_key == "":
            print("MFA code not provided..")
            mfa_key = pyotp.TOTP(self.totp_key).now()
        totp.send_keys(mfa_key)
        # adjustment complete

        '''
        continue_btn = WebDriverWait(driver, 10).until(
            lambda x: x.find_element("xpath", '//*[@id="container"]/div/div/div[2]/form/div[3]/button'))
        continue_btn.click()
        '''

        time.sleep(1)

        url = driver.current_url
        print(url)
        initial_token = url.split('request_token=')[1]
        request_token = initial_token.split('&')[0]

        driver.close()

        kite = KiteConnect(api_key=self.api_key)
        # print(request_token)
        data = kite.generate_session(request_token, api_secret=self.api_secret)
        kite.set_access_token(data['access_token'])
        print(data['access_token'])

        return kite

    '''
    def login_http(self, mfa_key=""):
        # Get request id in response
        response = self.session.post(LOGIN_URL, data={'user_id': USERNAME, 'password': PASSWORD})
        request_id = json.loads(response.text)['data']['request_id']

        if mfa_key == "":
            print("MFA code not provided..")
            mfa_key = pyotp.TOTP(self.totp_key).now()
        response_1 = self.session.post(TWOFA_URL, data={'user_id': USERNAME,
                                                        'request_id': request_id,
                                                        'twofa_value': mfa_key,
                                                        'twofa_type': 'totp'})

        kite = KiteConnect(api_key=self.api_key)
        kite_url = kite.login_url()
        print(kite_url)

        try:
            self.session.get(kite_url)
        except Exception as e:
            e_msg = str(e)
            request_token = e_msg.split('request_token=')[1].split(' ')[0].split('&action')[0]
            print('Successful Login with Request Token:{}'.format(request_token))
            access_token = kite.generate_session(request_token, API_SECRET)['access_token']
            kite.set_access_token(access_token)
            return kite
    '''

