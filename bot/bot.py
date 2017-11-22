import random

from django.conf import settings

from bot import insta_urls
from bot.mixins import BotSupportMixin
from bot.client import InstaClient
from bot.errors import InstaError


class Bot(BotSupportMixin):
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
        self.unfollow_count = 0
        self.series_errors = 0

        self.client = InstaClient(self.user_settings.get('use_ip'))

        self._log(
            f'\nInstabot for user: {user} was initialized.'
            f'\nLikes per day: {self.user_settings.get("likes_per_day", 1000)}. Follow ratio: 1/{self.follow_ratio}'
            f'\nUsing IP: {self.client.external_ip_address}',
            'info'
        )

    def _login(self):
        base_page = self.client.session.get(url=insta_urls.url_base)
        self.client.session.headers['X-CSRFToken'] = base_page.cookies['csrftoken']
        self._wait(2)

        login = self.client.session.post(url=insta_urls.url_login, data=self.log_pass_pair, allow_redirects=True)
        self.client.session.headers['X-CSRFToken'] = login.cookies['csrftoken']
        self.csrf_token = login.cookies['csrftoken']

        if login.status_code == 200:
            self.login_status = True
            self._log(f'Login was successful!')
            self._log(f'Using X-CSRFToken: {login.cookies["csrftoken"]}')
        else:
            raise InstaError(f'Login failed!')

        self._record_user_id()
        self._wait(2)

    def _logout(self):
        request = self.client.session.post(url=insta_urls.url_logout, data={'csrfmiddlewaretoken': self.csrf_token})
        if request.status_code in [302, 200]:
            self._log(
                f'Successfully logged out. '
                f'Liked: {self.like_count}. Followed: {self.follow_count}. Unfollowed: {self.unfollow_count}',
                'info'
            )
            self.login_status = False
        else:
            self._log(f'Failed to log out', 'error')

    def _record_user_id(self):
        response = self.client.request(url=insta_urls.url_user.format(self.username))
        if response.status_code == 200:
            self.user_id = response.json()['user']['id']
            self._log(f'User id: {self.user_id}')
        else:
            self._log(f'Failed to get user id')

    def _get_main_page(self):
        return self.client.session.get(url=insta_urls.url_base)

    def _get_media_by_tag(self, tag: str) -> list:
        """
        Return list of Rough media data from Instagram
        """
        self._check_login()

        response = self.client.session.get(insta_urls.url_tag.format(tag))

        if response.status_code == 200:
            self._log(f'Got media by tag: {tag}')
            return response.json()['tag']['media']['nodes']
        else:
            self._log(f'Failed to get media by tag: {tag}. Error text: {response.text}', 'error')
            return list()

    def _get_media(self, media_id: str) -> dict:
        self._check_login()

        response = self.client.session.get(insta_urls.url_media.format(media_id))

        if response.status_code == 200:
            self._log(f'Got info about media id: {media_id}')
            self.save_to_file(str(response.json()), 'media_info.js')
            return response.json()['graphql']['shortcode_media']
        else:
            self._log(f'Failed to info about media_id: {media_id}. Error text: {response.text}.', 'error')
            return dict()

    def _get_user(self, username: str) -> dict:
        self._check_login()

        response = self.client.session.get(insta_urls.url_user.format(username))

        if response.status_code == 200:
            self._log(f'Got info about user: {username}')
            self.save_to_file(str(response.json()), 'user_info.js')
            return response.json()
        else:
            self._log(f'Failed to get info about user: {username}. Error text: {response.text}.', 'error')
            return dict()

    def _like(self, media_id: str):
        self._check_login()

        response = self.client.session.post(insta_urls.url_likes.format(media_id))

        if response.status_code == 200:
            self._log(f'Liked media: {media_id}')
            self.like_count += 1
        else:
            self._log(f'Failed to like media: {media_id}. Error text: {response.text}.', 'error')

    def _follow(self, user_id: str):
        self._check_login()

        response = self.client.session.post(insta_urls.url_follow.format(user_id))

        if response.status_code == 200:
            self._log(f'Followed user_id: {user_id}')
            self.follow_count += 1
        else:
            self._log(f'Failed to follow user_id: {user_id}. Error text: {response.text}.', 'error')

    def _unfollow(self, user_id: str):
        self._check_login()

        response = self.client.session.post(insta_urls.url_unfollow.format(user_id))

        if response.status_code == 200:
            self._log(f'Unfollowed user_id: {user_id}')
            self.unfollow_count += 1
        else:
            self._log(f'Failed to unfollow user_id: {user_id}. Error text: {response.text}.', 'error')

    def _get_following(self, user_id: str = None) -> dict:
        self._check_login()
        user_id = user_id or self.user_id

        response = self.client.session.get(
            url=insta_urls.url_query,
            params={
                'query_id': '17874545323001329',
                'variables': {
                    'id': user_id,
                    'first': 100
                }
            },
            urlencode=True
        )

        if response.status_code == 200:
            self._log(f'Got followers for user: {user_id}')
            return response.json()['data']['user']['edge_follow']
        else:
            self._log(f'Failed to get followers for user: {user_id}. Error text: {response.text}', 'error')
            return dict()

    def _unfollow_loop(self):
        following = self._get_following()
        self.save_to_file(str(following), 'following.json')
        if following and following['count'] < 30:
            return  # Do nothing if we have less than 30 followers or there was an error in receiving

    def _start_loop(self):
        while True:
            for media in self._get_media_by_tag(random.choice(self.user_settings['tags'])):
                if media['likes']['count'] > 30:
                    self._log(f'Miss media. Like counter: {media["likes"]["count"]}')
                    continue
                if media['owner']['id'] == self.user_id:
                    self._log(f'Miss media. It\'s your media :)')
                    continue

                self._like(media['id'])
                if random.randint(1, self.follow_ratio) == 1:
                    self._follow(media['owner']['id'])

                self._wait(self.like_wait_interval)
            self._unfollow_loop()
            self._wait()

    def run(self):
        # self._fake_login('uQ46Uk7uMEcSsvXzdWvPtebxDEhYtam8')
        try:
            self._login()
            self._start_loop()
        except KeyboardInterrupt:
            self._log('Keyboard interruption', 'info')
        except InstaError as err:
            self._log(f'Exception: {str(err)}', 'error')
        except Exception as err:
            self._log(f'Any other exception. Err: {str(err)}', 'error')
        finally:
            self._logout()
