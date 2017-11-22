import logging

import codecs
import os
import random
from time import sleep

from django.conf import settings

logger = logging.getLogger('bot')


class BotSupportMixin:
    """
    Support methods for Bot
    All variables defined below, should be defined in __init__ in Bot
    """
    username = None
    series_errors = None
    client = None
    csrf_token = None

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

    def _wait(self, secs: int = None):
        secs_to_wait = secs or random.randint(1, 5)
        sleep(secs_to_wait)

    def _log(self, message: str, logger_name: str = 'debug'):
        getattr(logger, logger_name)(f'User: {self.username}. {message}')

        if logger_name == 'error':
            self.series_errors += 1
        else:
            self.series_errors = 0

        if self.series_errors >= 3:
            logger.error(f'User: {self.username}. Three errors in a row. Wait an hour for further processing')
            self._wait(60 * 30)
