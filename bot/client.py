import logging
from http.cookies import SimpleCookie
import json

import requests
from requests_toolbelt.adapters import source

from bot import insta_urls
from bot.utils import retry

logger = logging.getLogger('bot.client')


class InstaClient:
    def __init__(self, use_ip: str = None):
        self.session = InstabotSession()
        if use_ip is not None:
            new_ip = source.SourceAddressAdapter(use_ip)
            self.session.mount('http://', new_ip)
            self.session.mount('https://', new_ip)

        self.external_ip_address = self._get_external_ip_address()

        self._set_default_cookies()
        self._set_default_headers()

    def request(self, url: str, **kwargs):
        headers = kwargs.pop('headers', {})
        params = kwargs.pop('params', {})
        data = kwargs.pop('data', None)
        method = kwargs.pop('method', 'get').lower()

        return getattr(self.session, method.lower())(
            url=url,
            data=json.dumps(data),
            headers=headers,
            params=params,
            **kwargs
        )

    def _handle_response(self, response: requests.Response, return_json: bool):
        response.raise_for_status()

        if return_json:
            return response.json()
        else:
            return response.text

    def cookie_converter(self, raw_data: str) -> dict:
        cookie = SimpleCookie()
        cookie.load(raw_data)

        cookies = {}
        for key, morsel in cookie.items():
            cookies[key] = morsel.value

        return cookies

    def _set_default_cookies(self):
        self.session.cookies.update({
            'sessionid': '',
            'mid': '',
            'ig_pr': '1',
            'ig_vw': '1920',
            'csrftoken': '',
            's_network': '',
            'ds_user_id': ''
        })

    def _set_default_headers(self):
        self.session.headers.update({
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.6,en;q=0.4',
            'Connection': 'keep-alive',
            'Content-Length': '0',
            'Host': 'www.instagram.com',
            'Origin': 'https://www.instagram.com',
            'Referer': 'https://www.instagram.com/',
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/48.0.2564.103 Safari/537.36",
            'X-Instagram-AJAX': '1',
            'X-Requested-With': 'XMLHttpRequest'
        })

    def _get_external_ip_address(self):
        external_ip = 'unknown'
        try:
            external_ip = self.session.get(insta_urls.url_external_ip).json()['ip']
        finally:
            return external_ip


class InstabotSession(requests.Session):
    @retry(exceptions=requests.exceptions.RequestException, logger=logger)
    def request(self, *args, **kwargs):
        return super().request(*args, **kwargs)
