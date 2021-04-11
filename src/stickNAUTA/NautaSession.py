from __future__ import (annotations)

from re import (search)

from lxml import (html)
from requests import (Session)


class NautaSession(object):
    __nauta_homepage_url: str = 'https://secure.etecsa.net:8443/'
    __nauta_login_url: str = 'https://secure.etecsa.net:8443/LoginServlet'
    __nauta_query_url: str = 'https://secure.etecsa.net:8443/EtecsaQueryServlet'
    __nauta_logout_url: str = 'https://secure.etecsa.net:8443/LogoutServlet'
    __session: Session
    __username: str
    __password: str
    __wlanuserip: str
    __CSRFHW: str
    __ATTRIBUTE_UUID: str

    def __init__(self, username: str, password: str) -> None:
        if type(username) is not str:
            raise TypeError('username must be a str().')
        elif type(password) is not str:
            raise TypeError('password must be a str().')

        if not username.endswith(('@nauta.com.cu', '@nauta.co.cu')):
            raise ValueError('username is not valid. It must end with @nauta.com.cu or @nauta.co.cu.')

        self.__username = username
        self.__password = password

        self.__session = Session()

        html_tree = html.fromstring(self.__session.get(self.__nauta_homepage_url).text)
        self.__wlanuserip = html_tree.xpath('//*[@id="wlanuserip"]')[0].value
        self.__CSRFHW = html_tree.xpath('//*[@name="CSRFHW"]')[0].value

    def __enter__(self) -> NautaSession:
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.logout()

    def login(self) -> None:
        response = self.__session.post(self.__nauta_login_url, {
            'username': self.__username,
            'password': self.__password,
            'wlanuserip': self.__wlanuserip,
            'CSRFHW': self.__CSRFHW,
            'lang': 'en_EN'
        })

        if not response.ok:
            raise RuntimeError(f'Login failure with HTTP code: {response.status_code} and reason: "{response.reason}".')

        if 'online.do' not in response.url:
            reason = search(r'alert\("(?P<_>[^"]*?)"\)', response.text).group(1)
            raise RuntimeError(f'Login failure reason: "{reason}".')

        self.__ATTRIBUTE_UUID = search(r'ATTRIBUTE_UUID=(\w+)&CSRFHW=', response.text).group(1)

    def logout(self) -> None:
        response = self.__session.get(f'{self.__nauta_logout_url}?'
                                      f'username={self.__username}&'
                                      f'wlanuserip={self.__wlanuserip}&'
                                      f'CSRFHW={self.__CSRFHW}&'
                                      f'ATTRIBUTE_UUID={self.__ATTRIBUTE_UUID}')

        if not response.ok:
            raise RuntimeError(
                f'Logout failure with HTTP code: {response.status_code} and reason: "{response.reason}".')

        if "SUCCESS" not in response.text:
            raise RuntimeError(f'Logout failure reason: "{response.text}".')

    def get_remaining_time(self) -> str:
        response = self.__session.post(self.__nauta_query_url, {
            'op': 'getLeftTime',
            'username': self.__username,
            'wlanuserip': self.__wlanuserip,
            'CSRFHW': self.__CSRFHW,
            'ATTRIBUTE_UUID': self.__ATTRIBUTE_UUID
        })

        if not response.ok:
            raise RuntimeError(
                f'Failed to get user data (remaining_time) with HTTP code: {response.status_code}, '
                f'reason: "{response.reason}".')

        remaining_time = response.text
        return remaining_time

    def get_credit(self) -> str:
        response = self.__session.post(self.__nauta_query_url, {
            'username': self.__username,
            'password': self.__password,
            'wlanuserip': self.__wlanuserip,
            'CSRFHW': self.__CSRFHW,
            'lang': 'en_EN'
        })

        if not response.ok:
            raise RuntimeError(f'Failed to get user data (credit) with HTTP code: {response.status_code}, '
                               f'reason: "{response.reason}".')

        if 'secure.etecsa.net' not in response.url:
            reason = search(r'alert\("(?P<_>[^"]*?)"\)', response.text).group(1)
            raise RuntimeError(f'Failed to get user data (credit) reason: "{reason}".')

        credit = html.fromstring(response.text).xpath('//*[@id="sessioninfo"]/tbody/tr[2]/td[2]/text()')[0][13:-13]
        return credit
