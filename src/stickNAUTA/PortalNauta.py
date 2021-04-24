from json import (dump, load)
from re import (search)

from lxml import (html)
from requests import (Session)
from requests.utils import (dict_from_cookiejar, cookiejar_from_dict)


class PortalNauta(object):
    __portal_nauta_homepage_url: str = 'https://www.portal.nauta.cu/'
    __portal_nauta_login_url: str = 'https://www.portal.nauta.cu/user/login'
    __portal_nauta_user_url: str = 'https://www.portal.nauta.cu/useraaa'
    __portal_nauta_captcha: str = 'https://www.portal.nauta.cu/captcha'
    __language: str
    __session: Session
    __username: str
    __password: str
    __csrf: str
    __account_data: dict = None

    def __init__(self, username: str, password: str, lang_english: bool = True):
        if type(username) is not str:
            raise TypeError('username must be a str().')
        elif type(password) is not str:
            raise TypeError('password must be a str().')

        if not username.endswith(('@nauta.com.cu', '@nauta.co.cu')):
            raise ValueError('username is not valid. It must end with @nauta.com.cu or @nauta.co.cu.')

        self.__username = username
        self.__password = password

        self.__language = 'en-en' if lang_english else 'es-es'

        self.__session = Session()
        self.__session.headers['User-Agent'] = 'python-requests'

        response = self.__session.get(f'{self.__portal_nauta_login_url}/{self.__language}')
        if not response.ok:
            raise RuntimeError(f'Failed to init session with HTTP code: {response.status_code}, '
                               f'reason: "{response.reason}".')

        html_tree = html.fromstring(response.text)
        self.__csrf = html_tree.xpath('//*[@name="csrf"]')[0].value

    def get_captcha_image(self) -> bytes:
        response = self.__session.get(self.__portal_nauta_captcha)
        if not response.ok:
            raise RuntimeError(f'Failed to get captcha with HTTP code: {response.status_code}, '
                               f'reason: "{response.reason}".')
        return response.content

    def submit_captcha(self, captcha: str) -> None:
        if not type(captcha) is str:
            raise TypeError('captcha must be a str().')

        response = self.__session.post(self.__portal_nauta_login_url, {
            'csrf': self.__csrf,
            'login_user': self.__username,
            'password_user': self.__password,
            'captcha': captcha,
            'btn_submit': ''
        })
        if not response.ok:
            raise RuntimeError(f'Failed to submit CAPTCHA with HTTP code: {response.status_code}, '
                               f'reason: "{response.reason}".')

        if response.url == self.__portal_nauta_login_url:
            main_error = search(r"toastr.error\('<ul><li class=\"msg_error\">(.*)<ul>", response.text)
            if main_error:
                derived_errors = search(r"<li class=\"sub-message\">(.*)</li></ul></li></ul>'", response.text) \
                    .group(1).split('</li><li class="sub-message">')
                error_description = f'"{derived_errors[0]}"'
                for error in derived_errors[1:]:
                    error_description += f', "{error}"'

                raise RuntimeError(f'Failed to submit CAPTCHA code with error: "{main_error.group(1)}", '
                                   f'description: {error_description}.')

        self.__account_data = {}

    def recharge_account(self, recharge_code: str) -> None:
        if not self.__account_data:
            raise AttributeError('This method is not available until a valid CAPTCHA is submitted!')

        if not type(recharge_code) is str:
            raise TypeError('recharge_dode must be a str().')
        elif not recharge_code.isdigit():
            raise ValueError('recharge_code chars must be all digits.')
        elif not 12 <= len(recharge_code) <= 16:
            raise ValueError('recharge_code must be between 12 and 16 digits long.')

        response = self.__session.post(self.__portal_nauta_login_url, {
            'csrf': self.__csrf,
            'recharge_code': recharge_code,
            'btn_submit': ''
        })
        if not response.ok:
            raise RuntimeError(f'Failed to post recharge code with HTTP code: {response.status_code}, '
                               f'reason: "{response.reason}".')

        main_error = search(r"toastr.error\('<ul><li class=\"msg_error\">(.*)<ul>", response.text)
        if main_error:
            derived_errors = search(r"<li class=\"sub-message\">(.*)</li></ul></li></ul>'", response.text) \
                .group(1).split('</li><li class="sub-message">')
            error_description = f'"{derived_errors[0]}"'
            for error in derived_errors[1:]:
                error_description += f', "{error}"'

            raise RuntimeError(f'Failed to post recharge code with error: "{main_error.group(1)}", '
                               f'description: {error_description}.')

    def change_account_password(self, new_password: str) -> None:
        if not self.__account_data:
            raise AttributeError('This method is not available until a valid CAPTCHA is submitted!')

        if not type(new_password) is str:
            raise TypeError('new_password must be a str().')

        response = self.__session.post(f'{self.__portal_nauta_user_url}/change_password', {
            'csrf': self.__csrf,
            'old_password': self.__password,
            'new_password': new_password,
            'repeat_new_password': new_password,
            'btn_submit': ''
        })
        if not response.ok:
            raise RuntimeError(f'Failed to change password code with HTTP code: {response.status_code}, '
                               f'reason: "{response.reason}".')

        main_error = search(r"toastr.error\('<ul><li class=\"msg_error\">(.*)<ul>", response.text)
        if main_error:
            derived_errors = search(r"<li class=\"sub-message\">(.*)</li></ul></li></ul>'", response.text) \
                .group(1).split('</li><li class="sub-message">')
            error_description = f'"{derived_errors[0]}"'
            for error in derived_errors[1:]:
                error_description += f', "{error}"'

            raise RuntimeError(f'Failed to post recharge code with error: "{main_error.group(1)}", '
                               f'description: {error_description}.')

    def change_email_password(self, old_password: str, new_password: str) -> None:
        if not self.__account_data:
            raise AttributeError('This method is not available until a valid CAPTCHA is submitted!')

        if not type(old_password) is str:
            raise TypeError('old_password must be a str().')
        elif not type(new_password) is str:
            raise TypeError('new_password must be a str().')

        response = self.__session.post(f'{self.__portal_nauta_homepage_url}/email/change_password', {
            'csrf': self.__csrf,
            'old_password': old_password,
            'new_password': new_password,
            'repeat_new_password': new_password,
            'btn_submit': ''
        })
        if not response.ok:
            raise RuntimeError(f'Failed to change password code with HTTP code: {response.status_code}, '
                               f'reason: "{response.reason}".')

        main_error = search(r"toastr.error\('<ul><li class=\"msg_error\">(.*)<ul>", response.text)
        if main_error:
            derived_errors = search(r"<li class=\"sub-message\">(.*)</li></ul></li></ul>'", response.text) \
                .group(1).split('</li><li class="sub-message">')
            error_description = f'"{derived_errors[0]}"'
            for error in derived_errors[1:]:
                error_description += f', "{error}"'

            raise RuntimeError(f'Failed to post recharge code with error: "{main_error.group(1)}", '
                               f'description: {error_description}.')

    def transfer_balance(self, target_account: str, amount: float):
        if not self.__account_data:
            raise AttributeError('This method is not available until a valid CAPTCHA is submitted!')

        if not type(target_account) is str:
            raise TypeError('target_account must be a str().')
        elif not type(amount) is float:
            raise TypeError('amount must be a float().')

        if not target_account.endswith(('@nauta.com.cu', '@nauta.co.cu')):
            raise ValueError('username is not valid. It must end with @nauta.com.cu or @nauta.co.cu.')

        response = self.__session.post(f'{self.__portal_nauta_user_url}/transfer_balance', {
            'csrf': self.__csrf,
            'transfer': amount,
            'password_user': self.__password,
            'id_cuenta': target_account,
            'action': 'checkdata'
        })
        if not response.ok:
            raise RuntimeError(f'Failed to transfer money with HTTP code: {response.status_code}, '
                               f'reason: "{response.reason}".')

        main_error = search(r"toastr.error\('<ul><li class=\"msg_error\">(.*)<ul>", response.text)
        if main_error:
            derived_errors = search(r"<li class=\"sub-message\">(.*)</li></ul></li></ul>'", response.text) \
                .group(1).split('</li><li class="sub-message">')
            error_description = f'"{derived_errors[0]}"'
            for error in derived_errors[1:]:
                error_description += f', "{error}"'

            raise RuntimeError(f'Failed to post recharge code with error: "{main_error.group(1)}", '
                               f'description: {error_description}.')

    def get_account_data(self, refresh: bool = True) -> dict:
        if not self.__account_data:
            raise AttributeError('This property is not available until a valid CAPTCHA is submitted!')

        if refresh or not len(self.__account_data.keys()):
            response = self.__session.get(f'{self.__portal_nauta_user_url}/user_info')
            if not response.ok:
                raise RuntimeError(f'Failed to get account info with HTTP code: {response.status_code}, '
                                   f'reason: "{response.reason}".')

            html_tree = html.fromstring(response.text)
            self.__account_data = {
                'username': html_tree.xpath('//*[@id="content"]/div[2]/div/div/div/div[2]/div/p/text()')[0],
                'blocking_date': html_tree.xpath('//*[@id="content"]/div[2]/div/div/div/div[3]/div[1]/p/text()')[0],
                'elimination_date': html_tree.xpath('//*[@id="content"]/div[2]/div/div/div/div[3]/div[2]/p/text()')[0],
                'account_type': html_tree.xpath('//*[@id="content"]/div[2]/div/div/div/div[4]/div[1]/p/text()')[0],
                'service_type': html_tree.xpath('//*[@id="content"]/div[2]/div/div/div/div[4]/div[2]/p/text()')[0],
                'available_balance': html_tree.xpath('//*[@id="content"]/div[2]/div/div/div/div[5]/div[1]/p/text()')[0],
                'remaining_time': html_tree.xpath('//*[@id="content"]/div[2]/div/div/div/div[5]/div[2]/p/text()')[0],
                'email_account': html_tree.xpath('//*[@id="content"]/div[2]/div/div/div/div[6]/div/p/text()')[0]
            }

        return self.__account_data

    def get_connection_details(self) -> dict:
        if not self.__account_data:
            raise AttributeError('This method is not available until a valid CAPTCHA is submitted!')

        connection_details = {}
        response = self.__session.get(f'{self.__portal_nauta_user_url}/service_detail')
        if not response.ok:
            raise RuntimeError(f'Failed to get connection details timestamp with HTTP code: {response.status_code}, '
                               f'reason: "{response.reason}".')

        for timestamp in html.fromstring(response.text).xpath('//*[@name="year_month"]/option'):
            year_month = timestamp.attrib['value']
            connection_details[year_month] = {}

            response = self.__session.post(f'{self.__portal_nauta_user_url}/service_detail_summary', {
                'csrf': self.__csrf,
                'year_month': year_month,
                'list_type': 'service_detail'
            })
            if not response.ok:
                raise RuntimeError(
                    f'Failed to get connection details summary with HTTP code: {response.status_code}, '
                    f'reason: "{response.reason}".')

            summary_data = html.fromstring(response.text).xpath('//*[@class="card-stats-number"]/text()')
            connection_details[year_month]['connections'] = summary_data[0]
            connection_details[year_month]['total_time'] = summary_data[1]
            connection_details[year_month]['total_import'] = summary_data[2]
            connection_details[year_month]['upload_traffic'] = summary_data[3]
            connection_details[year_month]['download_traffic'] = summary_data[4]
            connection_details[year_month]['total_traffic'] = summary_data[5]
            connection_details[year_month]['all_sessions'] = []

            for i in range(1, int(int(connection_details[year_month]['connections']) / 15) + 2):
                response = self.__session.get(f"{self.__portal_nauta_user_url}/service_detail_list/"
                                              f"{year_month}/{connection_details[year_month]['connections']}/{i}")
                if not response.ok:
                    raise RuntimeError(
                        f'Failed to get all sessions connection details with HTTP code: {response.status_code}, '
                        f'reason: "{response.reason}".')

                rows = html.fromstring(response.text).xpath('/html/body/div[1]/div/table/tr/td/text()')
                for j in range(0, len(rows), 6):
                    connection_details[year_month]['all_sessions'].append({
                        'start_datetime': rows[j],
                        'end_datetime': rows[j + 1],
                        'duration': rows[j + 2],
                        'upload_traffic': rows[j + 3],
                        'download_traffic': rows[j + 4],
                        'import': rows[j + 5],
                    })

        return connection_details

    def get_recharge_details(self) -> dict:
        if not self.__account_data:
            raise AttributeError('This method is not available until a valid CAPTCHA is submitted!')

        recharge_details = {}
        response = self.__session.get(f'{self.__portal_nauta_user_url}/recharge_detail')
        if not response.ok:
            raise RuntimeError(f'Failed to get recharge details timestamp with HTTP code: {response.status_code}, '
                               f'reason: "{response.reason}".')

        for timestamp in html.fromstring(response.text).xpath('//*[@name="year_month"]/option'):
            year_month = timestamp.attrib['value']
            recharge_details[year_month] = {}

            response = self.__session.post(f'{self.__portal_nauta_user_url}/recharge_detail_summary', {
                'csrf': self.__csrf,
                'year_month': year_month,
                'list_type': 'service_detail'
            })
            if not response.ok:
                raise RuntimeError(
                    f'Failed to get recharge details summary with HTTP code: {response.status_code}, '
                    f'reason: "{response.reason}".')

            summary_data = html.fromstring(response.text).xpath('//*[@class="card-stats-number"]/text()')
            recharge_details[year_month]['recharges'] = summary_data[0]
            recharge_details[year_month]['total_import'] = summary_data[1]
            recharge_details[year_month]['all_recharges'] = []

            for i in range(1, int(int(recharge_details[year_month]['recharges']) / 15) + 2):
                response = self.__session.get(f"{self.__portal_nauta_user_url}/recharge_detail_list/"
                                              f"{year_month}/{recharge_details[year_month]['recharges']}/{i}")
                if not response.ok:
                    raise RuntimeError(
                        f'Failed to get all recharges details with HTTP code: {response.status_code}, '
                        f'reason: "{response.reason}".')

                rows = html.fromstring(response.text).xpath('/html/body/div[1]/div/table/tr/td/text()')
                for j in range(0, len(rows), 4):
                    recharge_details[year_month]['all_recharges'].append({
                        'datetime': rows[j],
                        'import': rows[j + 1],
                        'channel': rows[j + 2],
                        'type': rows[j + 3]
                    })

        return recharge_details

    def get_transfer_details(self) -> dict:
        if not self.__account_data:
            raise AttributeError('This method is not available until a valid CAPTCHA is submitted!')

        transfer_details = {}
        response = self.__session.get(f'{self.__portal_nauta_user_url}/transfer_detail')
        if not response.ok:
            raise RuntimeError(f'Failed to get transfer details timestamp with HTTP code: {response.status_code}, '
                               f'reason: "{response.reason}".')

        for timestamp in html.fromstring(response.text).xpath('//*[@name="year_month"]/option'):
            year_month = timestamp.attrib['value']
            transfer_details[year_month] = {}

            response = self.__session.post(f'{self.__portal_nauta_user_url}/transfer_detail_summary', {
                'csrf': self.__csrf,
                'year_month': year_month,
                'list_type': 'service_detail'
            })
            if not response.ok:
                raise RuntimeError(
                    f'Failed to get transfer details summary with HTTP code: {response.status_code}, '
                    f'reason: "{response.reason}".')

            summary_data = html.fromstring(response.text).xpath('//*[@class="card-stats-number"]/text()')
            transfer_details[year_month]['transfers'] = summary_data[0]
            transfer_details[year_month]['total_import'] = summary_data[1]
            transfer_details[year_month]['all_transfers'] = []

            for i in range(1, int(int(transfer_details[year_month]['transfers']) / 15) + 2):
                response = self.__session.get(f"{self.__portal_nauta_user_url}/transfer_detail_list/"
                                              f"{year_month}/{transfer_details[year_month]['transfers']}/{i}")
                if not response.ok:
                    raise RuntimeError(
                        f'Failed to get all transfer details with HTTP code: {response.status_code}, '
                        f'reason: "{response.reason}".')

                rows = html.fromstring(response.text).xpath('/html/body/div[1]/div/table/tr/td/text()')
                for j in range(0, len(rows), 3):
                    transfer_details[year_month]['all_transfers'].append({
                        'datetime': rows[j],
                        'import': rows[j + 1],
                        'target_account': rows[j + 2]
                    })

        return transfer_details

    def get_session_data(self) -> dict:
        if not self.__account_data:
            raise RuntimeError('Cannot get session data since user is not logged in. Submit a valid CAPTCHA first!')

        session_data = {
            'username': self.__username,
            'cookies': dict_from_cookiejar(self.__session.cookies),
        }
        return session_data

    def set_session_data(self, session_data: dict) -> None:
        if self.__account_data:
            raise RuntimeError('Cannot set session data since user is logged in. Submit a valid CAPTCHA first!')

        required_keys = ['username', 'cookies']
        for key in required_keys:
            if key not in session_data.keys():
                raise ValueError(f'session_data kas not required key: \'{key}\'.')

        if not session_data['username'] == self.__username:
            raise ValueError('Session data is not for this account.')

        self.__session.cookies = cookiejar_from_dict(session_data['cookies'])
        self.__account_data = {}

    def save_session_data_to_file(self, file_path: str) -> None:
        with open(file_path, 'w') as file:
            dump(self.get_session_data(), file)

    def load_session_data_from_file(self, file_path: str) -> None:
        with open(file_path, 'r') as file:
            session_data = load(file)
            if isinstance(session_data, dict):
                self.set_session_data(session_data)
            else:
                raise ValueError('File does not contain a dict and therefore not a session data.')
