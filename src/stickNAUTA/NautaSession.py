from __future__ import (annotations)

from ctypes import (Union)
from re import (search)

from lxml import (html)
from requests import (Session)


class NautaSession(object):
    __nauta_homepage_url: str = 'https://secure.etecsa.net:8443/'
    __nauta_login_url: str = 'https://secure.etecsa.net:8443/LoginServlet'
    __nauta_query_url: str = 'https://secure.etecsa.net:8443/EtecsaQueryServlet'
    __nauta_logout_url: str = 'https://secure.etecsa.net:8443/LogoutServlet'
    __logged_in: bool = False
    __user_information: dict = None
    __language: str
    __session: Session
    __username: str
    __password: str
    __wlanuserip: str
    __CSRFHW: str
    __ATTRIBUTE_UUID: str

    def __init__(self, username: str, password: str, acquire_user_info: bool = True, lang_english: bool = True) -> None:
        if type(username) is not str:
            raise TypeError('username must be a str().')
        elif type(password) is not str:
            raise TypeError('password must be a str().')

        if not username.endswith(('@nauta.com.cu', '@nauta.co.cu')):
            raise ValueError('username is not valid. It must end with @nauta.com.cu or @nauta.co.cu.')

        self.__username = username
        self.__password = password

        self.__language = 'en_US' if lang_english else 'es_ES'

        self.__session = Session()

        response = self.__session.get(self.__nauta_homepage_url)
        if not response.ok:
            raise RuntimeError(f'Failed to init session with HTTP code: {response.status_code}, '
                               f'reason: "{response.reason}".')

        html_tree = html.fromstring(response.text)
        self.__wlanuserip = html_tree.xpath('//*[@id="wlanuserip"]')[0].value
        self.__CSRFHW = html_tree.xpath('//*[@name="CSRFHW"]')[0].value

        if acquire_user_info:
            response = self.__session.post(self.__nauta_query_url, {
                'username': self.__username,
                'password': self.__password,
                'wlanuserip': self.__wlanuserip,
                'CSRFHW': self.__CSRFHW,
                'lang': self.__language
            })

            if not response.ok:
                raise RuntimeError(f'Failed to get user data (credit) with HTTP code: {response.status_code}, '
                                   f'reason: "{response.reason}".')

            if 'secure.etecsa.net' not in response.url:
                reason = search(r'alert\("(?P<_>[^"]*?)"\)', response.text).group(1)
                raise RuntimeError(f'Failed to get user data (credit) reason: "{reason}".')

            html_tree = html.fromstring(response.text)
            account_state = html_tree.xpath('//*[@id="sessioninfo"]/tbody/tr[1]/td[2]/text()')[0][13:-12]
            credit = html_tree.xpath('//*[@id="sessioninfo"]/tbody/tr[2]/td[2]/text()')[0][13:-13]
            expiration_date = html_tree.xpath('//*[@id="sessioninfo"]/tbody/tr[3]/td[2]/text()')[0][13:-12]
            access_areas = html_tree.xpath('//*[@id="sessioninfo"]/tbody/tr[4]/td[2]/text()')[0][13:-12]
            sessions_data = html_tree.xpath('//*[@id="sesiontraza"]/tbody/tr/td/text()')

            self.__user_information = {
                'account_state': account_state,
                'credit': credit,
                'expiration_date': expiration_date,
                'access_areas': access_areas,
                'sessions': [
                    {
                        'start': sessions_data[0],
                        'end': sessions_data[1],
                        'duration': sessions_data[2]
                    },
                    {
                        'start': sessions_data[3],
                        'end': sessions_data[4],
                        'duration': sessions_data[5]
                    },
                    {
                        'start': sessions_data[6],
                        'end': sessions_data[7],
                        'duration': sessions_data[8]
                    }
                ]
            }

    def __enter__(self) -> NautaSession:
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.logout()

    def login(self) -> None:
        if self.__logged_in:
            raise RuntimeError('User is already logged in.')

        response = self.__session.post(self.__nauta_login_url, {
            'username': self.__username,
            'password': self.__password,
            'wlanuserip': self.__wlanuserip,
            'CSRFHW': self.__CSRFHW,
            'lang': self.__language
        })

        if not response.ok:
            raise RuntimeError(f'Login failure with HTTP code: {response.status_code} and reason: "{response.reason}".')

        if 'online.do' not in response.url:
            reason = search(r'alert\("(?P<_>[^"]*?)"\)', response.text).group(1)
            raise RuntimeError(f'Login failure reason: "{reason}".')

        self.__ATTRIBUTE_UUID = search(r'ATTRIBUTE_UUID=(\w+)&CSRFHW=', response.text).group(1)
        self.__logged_in = True

    def logout(self) -> None:
        if not self.__logged_in:
            raise RuntimeError('User is not logged in.')

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

        self.__logged_in = False
        self.__ATTRIBUTE_UUID = str()

    def get_user_info(self) -> dict:
        if not self.__user_information:
            raise AttributeError('NautaSession has no user information since acquire_user_info=False '
                                 'was passed to __init__.')
        return self.__user_information

    def get_remaining_time(self, in_seconds: bool = False) -> Union[str, int]:
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
        if in_seconds:
            (hours, minutes, seconds) = [int(number) for number in remaining_time.split(':')]
            remaining_time = hours * 3600 + minutes * 60 + seconds

        return remaining_time
