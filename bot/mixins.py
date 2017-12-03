import logging
import codecs
import os
import random
from time import sleep

import requests
from django.conf import settings

from bot import utils
from bot.errors import InstaError

logger = logging.getLogger('bot')


class BotSupportMixin:
    """
    Support methods for Bot
    All variables defined below, should be defined in __init__ in Bot
    """
    username = None
    series_errors = None
    ban_count = None
    client = None
    csrf_token = None
    login_status = None

    def fake_login(self, csrftoken: str):
        """Use instead of login, if already know the token and know that there wasn't logout previously"""
        self.client.session.headers['X-CSRFToken'] = csrftoken
        self.client.session.cookies['csrftoken'] = csrftoken
        self.csrf_token = csrftoken

    def save_to_file(self, data: str, filename: str = 'tmp.html'):
        """filename sample: tmp.html"""
        file_path = os.path.join(settings.HTML_SAMPLES_DIR_PATH, filename)
        with codecs.open(file_path, 'w', 'utf-16') as f:
            f.write(data)
        self._log(f'Content was written to file: {filename}')

    def _check_login(self):
        if self.login_status is False:
            raise InstaError(f'Is not logged in with user: {self.username}')

    def _wait(self, secs: int = None):
        secs_to_wait = secs or random.randint(1, 5)
        sleep(secs_to_wait)

    def _log(self, message: str, logger_name: str = 'debug'):
        getattr(logger, logger_name)(f'User: {self.username}. {message}')

        if logger_name == 'error':
            self.series_errors += 1
        else:
            self.series_errors = 0
            self.ban_count = 0

        if self.series_errors >= 3:
            logger.error(f'User: {self.username}. Three errors in a row. Wait an hour for further processing')
            self._wait(60 * 30)

    def _log_failed_response(self, response: requests.Response, err_message: str):
        if response.status_code // 100 == 4 and 'missing media' in response.text:
            self._log(f'{err_message}. Missing media', 'error')
        elif response.status_code // 100 == 4 and 'Подождите несколько минут' in response.text:
            self._log(f'{err_message}. Asked to wait a bit. Waiting 5 min', 'error')
            self._wait(60*5)
        elif response.status_code // 100 == 4 and 'Действие заблокировано' in utils.latin_decoder(response.text):
            self._log(f'{err_message}. Action was temporary blocked. Waiting 10 min', 'error')
            self._wait(60*10)
        elif response.status_code // 100 == 4 and 'вы злоупотребляли' in utils.latin_decoder(response.text):
            self.ban_count += 1
            self._log(f'{err_message}. Action was banned. Waiting 1 hour. Ban count {self.ban_count}', 'error')
            self._wait(60 * 60)
        elif response.status_code // 100 == 5:
            self._log(f'{err_message}. Server error', 'error')
        else:
            self._log(f'{err_message}. Error text: {response.text}. Error status: {response.status_code}', 'error')
