import codecs
import logging
import os
from time import sleep
import random

import requests
from django.conf import settings

from bot import urls
from bot.client import InstaParseClient
from bot.errors import InstaError

logger = logging.getLogger('bot')


class Bot:
    def __init__(self, user: str):
        if user not in settings.INSTA_USERS:
            raise InstaError(f'Can not find user: {user} in settings')

        self.username = settings.INSTA_USERS[user]['login']
        self.log_pass_pair = {
            'username': self.username.lower(),
            'password': settings.INSTA_USERS[user]['password']
        }

        self.login_status = False
        self.user_id = None
        self.csrf_token = None

        self.client = InstaParseClient(settings.INSTA_USERS[user].get('use_ip'))

    def _login(self):
        logger.debug(f'Trying to login as {self.username}')

        base_page = self.client.session.get(url=urls.url_base)
        self.client.session.headers['X-CSRFToken'] = base_page.cookies['csrftoken']
        self._wait()

        login = self.client.session.post(url=urls.url_login, data=self.log_pass_pair, allow_redirects=True)
        self.client.session.headers['X-CSRFToken'] = login.cookies['csrftoken']
        self.csrf_token = login.cookies['csrftoken']
        self._wait()

        self._check_login(login)
        self._record_user_id()

    def _logout(self):
        request = self.client.session.post(url=urls.url_logout, data={'csrfmiddlewaretoken': self.csrf_token})
        if request.status_code in [302, 200]:
            logger.info(f'Successfully log out for user: {self.username}')
            self.login_status = False
        else:
            logger.error(f'Failed to log out for user: {self.username}')

    def _check_login(self, login_response: requests.Response):
        if login_response.status_code == 200:
            self.login_status = True
            logger.info(f'Login with user: {self.username} was successful!')
            logger.debug(f'Using X-CSRFToken: {login_response.cookies["csrftoken"]}')
        else:
            raise Exception(f'Login with user: {self.username} failed!')

    def _record_user_id(self):
        response = self.client.request(url=urls.url_user.format(self.username))
        if response.status_code == 200:
            self.user_id = response.json()['user']['id']
            logger.debug(f'User id: {self.user_id}')
        else:
            logger.debug(f'Failed to get user id')

    def _get_main_page(self):
        return self.client.session.get(url=urls.url_base)

    def _fake_login(self, csrftoken: str):
        """Use instead of login, if already know the token and know that there wasn't logout previously"""
        self.client.session.headers['X-CSRFToken'] = csrftoken
        self.client.session.cookies['csrftoken'] = csrftoken
        self.csrf_token = csrftoken

    def save_to_file(self, data: str, filename: str = 'tmp.html'):
        """filename sample: tmp.html"""
        file_path = os.path.join(settings.HTML_SAMPLES_DIR_PATH, filename)
        with codecs.open(file_path, 'w', 'utf-16') as f:
            f.write(data)
        logger.debug(f'Content was written to file: {filename}')

    def _get_media_by_tag(self, tag: str) -> list:
        """Return list of Rough media data from Instagram"""
        if self.login_status is False:
            return list()

        response = self.client.session.get(urls.url_tag.format(tag))

        if response.status_code == 200:
            logger.debug(f'Got media by tag: {tag}')
            return list(response.json()['tag']['media']['nodes'])
        else:
            logger.debug('Failed to get media by tag: {tag}. Status code: {response.status_code}')
            return list()

    def _get_user(self, user_id: int) -> list:
        if self.login_status is False:
            return list()

        response = self.client.session.get(urls.url_user.format(user_id))

        if response.status_code == 200:
            logger.debug(f'Got info about user_id: {user_id}')
            self.save_to_file(str(response.json()), 'user_info.js')
            return response.json()
        else:
            logger.debug(f'Failed to info about user_id: {user_id}. Status code: {response.status_code}.')
            return list()

    def _like(self, media_id: str) -> bool:
        if self.login_status is False:
            return False

        response = self.client.session.post(urls.url_likes.format(media_id))

        if response.status_code == 200:
            logger.debug(f'Liked media: {media_id}')
            return True
        else:
            logger.debug(f'Failed to like media: {media_id}. Status code: {response.status_code}.')
            return False

    def _follow(self, user_id: str) -> bool:
        if self.login_status is False:
            return False

        response = self.client.session.post(urls.url_follow.format(user_id))

        if response.status_code == 200:
            logger.debug(f'Followed user_id: {user_id}')
            return True
        else:
            logger.debug(f'Failed to follow user_id: {user_id}. Status code: {response.status_code}.')
            return False

    def _wait(self, secs: int = None):
        secs_to_wait = secs or random.randint(2, 7)
        sleep(secs_to_wait)

    def run(self):
        self._login()
        current_media = self._get_media_by_tag(random.choice(settings.TAGS))
        self._like(current_media[2]['id'])
        self._follow(current_media[1]['owner']['id'])
        # self._get_user(current_media[1]['owner']['id'])  # Not working, need to get username
        # self._fake_login('uQ46Uk7uMEcSsvXzdWvPtebxDEhYtam8')
        self._logout()


# Todo [Max] [16/11/2017 13:24] Limit number of likes/follows per day
# Todo [Max] [16/11/2017 13:25] Write info to DB
