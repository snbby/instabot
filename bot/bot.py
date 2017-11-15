import codecs
import json
import logging
import os
import random
from time import sleep

import requests
from django.conf import settings

from bot import urls
from bot.client import InstaParseClient

logging.basicConfig(format='[%(asctime)s] [%(levelname)-5s] - %(message)s', level=logging.DEBUG)

logger = logging.getLogger('common')


class Bot:
    def __init__(self, username: str, password: str):
        self.username = username
        self.log_pass_pair = {
            'username': username.lower(),
            'password': password
        }
        self.login_status = False

        self.user_id = None
        self.csrf_token = None

        self.client = InstaParseClient()

    def _login(self):
        logger.debug(f'Trying to login as {self.username}')

        base_page = self.client.session.get(url=urls.url_base)
        print(f'Token: {base_page.cookies["csrftoken"]}')
        self.client.session.headers['X-CSRFToken'] = base_page.cookies['csrftoken']
        self._save_html_to_file(base_page.content.decode(), 'base_initial_page.html')
        sleep(random.randint(2, 7))

        login = self.client.session.post(url=urls.url_login, data=self.log_pass_pair, allow_redirects=True)
        print(f'Token: {login.cookies["csrftoken"]}')
        self.client.session.headers['X-CSRFToken'] = login.cookies['csrftoken']
        self.csrf_token = login.cookies['csrftoken']
        self._save_html_to_file(login.content.decode(), 'login_page.html')
        sleep(random.randint(2, 7))

        self._check_login(login)
        self._record_user_id()
        self._save_html_to_file(self._get_main_page().content.decode(), 'main_page.html')

    def _logout(self):
        r = self.client.session.post(url=urls.url_logout, data={'csrfmiddlewaretoken': self.csrf_token})
        logger.info(f'Successfully log out for login: {self.username}')
        self.login_status = False

        self._save_html_to_file(r.content.decode(), 'logout_page.html')

    def _fake_login(self, csrftoken: str):
        """Use instead of login, if already know the token and know that there wasn't logout previously"""
        self.client.session.headers['X-CSRFToken'] = csrftoken
        self.client.session.cookies['csrftoken'] = csrftoken
        self.csrf_token = csrftoken

    def _check_login(self, login_response: requests.Response):
        if login_response.status_code == 200:
            self.login_status = True
            logger.info(f'Login with user: {self.username} was successful!')
            logger.debug(f'Using X-CSRFToken: {login_response.cookies["csrftoken"]}')
        else:
            raise Exception(f'Login with user: {self.username} failed!')

    def _record_user_id(self):
        info_response = self.client.request(url=urls.url_user_detail.format(self.username))
        all_data = json.loads(info_response.text)
        self.user_id = all_data['user']['id']

        logger.debug(f'User id: {self.user_id}')

    def _get_main_page(self):
        return self.client.session.get(url=urls.url_base)

    def _save_html_to_file(self, data: str, filename: str):
        """filename sample: tmp.html"""
        file_path = os.path.join(settings.HTML_SAMPLES_DIR_PATH, filename)
        with codecs.open(file_path, 'w', 'utf-16') as f:
            f.write(data)
        logger.debug(f'Content was written to file: {filename}')

    def run(self):
        self._login()
        self._logout()



