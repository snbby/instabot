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

        self.user_settings = settings.INSTA_USERS[user]
        self.username = self.user_settings['login']
        self.log_pass_pair = {
            'username': self.username.lower(),
            'password': self.user_settings['password']
        }
        self.like_wait_interval = int(86400 / self.user_settings.get('likes_per_day', 1000))
        self.follow_ratio = int(
            self.user_settings.get('likes_per_day', 1000) / self.user_settings.get('follows_per_day', 100)
        )

        self.login_status = False
        self.user_id = None
        self.csrf_token = None

        self.like_count = 0
        self.follow_count = 0
        self.series_errors = 0

        self.client = InstaParseClient(settings.INSTA_USERS[user].get('use_ip'))

        self._log(
            f'\nInstabot for user: {user} was initialized.'
            f'\nLikes per day: {self.user_settings.get("likes_per_day", 1000)}. Follow ratio: 1/{self.follow_ratio}'
            f'\nUsing IP: {self.client.external_ip_address}',
            'info'
        )

    def _login(self):
        base_page = self.client.session.get(url=urls.url_base)
        self.client.session.headers['X-CSRFToken'] = base_page.cookies['csrftoken']
        self._wait(2)

        login = self.client.session.post(url=urls.url_login, data=self.log_pass_pair, allow_redirects=True)
        self.client.session.headers['X-CSRFToken'] = login.cookies['csrftoken']
        self.csrf_token = login.cookies['csrftoken']
        self._wait(2)

        self._check_login(login)
        self._record_user_id()

    def _logout(self):
        request = self.client.session.post(url=urls.url_logout, data={'csrfmiddlewaretoken': self.csrf_token})
        if request.status_code in [302, 200]:
            self._log(
                f'Successfully logged out. '
                f'Liked: {self.like_count}. Followed: {self.follow_count}',
                'info'
            )
            self.login_status = False
        else:
            self._log(f'Failed to log out', 'error')

    def _check_login(self, login_response: requests.Response):
        if login_response.status_code == 200:
            self.login_status = True
            self._log(f'Login was successful!')
            self._log(f'Using X-CSRFToken: {login_response.cookies["csrftoken"]}')
        else:
            raise Exception(f'Login failed!')

    def _record_user_id(self):
        response = self.client.request(url=urls.url_user.format(self.username))
        if response.status_code == 200:
            self.user_id = response.json()['user']['id']
            self._log(f'User id: {self.user_id}')
        else:
            self._log(f'Failed to get user id')

    def _get_main_page(self):
        return self.client.session.get(url=urls.url_base)

    def _get_media_by_tag(self, tag: str) -> list:
        """
        Return list of Rough media data from Instagram
        """
        if self.login_status is False:
            raise InstaError(f'Is not logged in with user: {self.username}')

        response = self.client.session.get(urls.url_tag.format(tag))

        if response.status_code == 200:
            self._log(f'Got media by tag: {tag}')
            return response.json()['tag']['media']['nodes']
        else:
            self._log(f'Failed to get media by tag: {tag}. Status code: {response.status_code}', 'error')
            return list()

    def _get_media(self, media_id: str) -> dict:
        if self.login_status is False:
            raise InstaError(f'Is not logged in with user: {self.username}')

        response = self.client.session.get(urls.url_media.format(media_id))

        if response.status_code == 200:
            self._log(f'Got info about media id: {media_id}')
            self.save_to_file(str(response.json()), 'media_info.js')
            return response.json()['graphql']['shortcode_media']
        else:
            self._log(f'Failed to info about media_id: {media_id}. Status code: {response.status_code}.', 'error')
            return dict()

    def _get_user(self, username: str) -> list:
        if self.login_status is False:
            raise InstaError(f'Is not logged in with user: {self.username}')

        response = self.client.session.get(urls.url_user.format(username))

        if response.status_code == 200:
            self._log(f'Got info about user: {username}')
            self.save_to_file(str(response.json()), 'user_info.js')
            return response.json()
        else:
            self._log(f'Failed to get info about user: {username}. Status code: {response.status_code}.', 'error')
            return list()

    def _like(self, media_id: str):
        if self.login_status is False:
            raise InstaError(f'Is not logged in with user: {self.username}')

        response = self.client.session.post(urls.url_likes.format(media_id))

        if response.status_code == 200:
            self._log(f'Liked media: {media_id}')
            self.like_count += 1
        else:
            self._log(f'Failed to like media: {media_id}. Status code: {response.status_code}.', 'error')

    def _follow(self, user_id: str):
        if self.login_status is False:
            raise InstaError(f'Is not logged in with user: {self.username}')

        response = self.client.session.post(urls.url_follow.format(user_id))

        if response.status_code == 200:
            self._log(f'Followed user_id: {user_id}')
            self.follow_count += 1
        else:
            self._log(f'Failed to follow user_id: {user_id}. Status code: {response.status_code}.', 'error')

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
            self._wait(60 * 60)

    def _start_loop(self):
        while True:
            for media in self._get_media_by_tag(random.choice(self.user_settings['tags'])):
                if media['is_video'] is True or media['likes']['count'] > 50:
                    self._log(f'Miss media. Is video: {media["is_video"]}. Like counter: {media["likes"]["count"]}')
                    continue
                if media['owner']['id'] == self.user_id:
                    self._log(f'Miss media. It\'s your media :)')
                    continue

                self._like(media['id'])
                if random.randint(1, self.follow_ratio) == 1:
                    self._follow(media['owner']['id'])

                self._wait(self.like_wait_interval)
            self._wait()

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

    def run(self):
        # self._fake_login('uQ46Uk7uMEcSsvXzdWvPtebxDEhYtam8')
        try:
            self._login()
            self._start_loop()
        except KeyboardInterrupt:
            self._log('Keyboard interruption', 'info')
        except Exception as err:
            self._log(f'Any other exception. Err: {str(err)}', 'error')
        finally:
            self._logout()
