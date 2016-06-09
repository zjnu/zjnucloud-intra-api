from collections import OrderedDict
import random
import re
import base64

from lxml import etree
import requests

from onecard.models import OneCardUser

# OneCard_URL
URL_LOGIN = 'http://ykt.zjnu.edu.cn/'
URL_MAIN = 'http://ykt.zjnu.edu.cn/Cardholder/Cardholder.aspx'
URL_ACCOUNT_DETAIL = 'http://ykt.zjnu.edu.cn/Cardholder/AccInfo.aspx'
URL_ACCOUNT_DETAIL_AVATAR = 'http://ykt.zjnu.edu.cn/Cardholder/ShowImage.aspx?AccNum='
URL_ACCOUNT_BALANCE = 'http://ykt.zjnu.edu.cn/Cardholder/AccBalance.aspx'
URL_ONLINE_BANK_CHARGE = 'http://ykt.zjnu.edu.cn/Cardholder/Onlinebank.aspx'
URL_ELECTRICITY_CHARGE = 'http://ykt.zjnu.edu.cn/Cardholder/SelfHelpElec.aspx'

# Session status code
STATUS_SUCCESS = 200
STATUS_LOGIN_FAILED = 403
STATUS_ERR_UNKNOWN = 101000
STATUS_ERR_PARAM = 101001
STATUS_EXCEED_BMOB_BIND_TIMES_LIMIT = 101002
STATUS_EXCEED_ONECARD_BIND_TIMES_LIMIT = 101003
STATUS_ONLINE_BANK_CHARGE_ERR_UNKNOWN = 101100
STATUS_ONLINE_BANK_CHARGE_INVALID_AMOUNT = 101101
STATUS_ONLINE_BANK_CHARGE_PAY_PASSWORD_WRONG = 101102

# Messages
MSG_SUCCESS = 'success'
MSG_LOGIN_FAILED = '登录失败，用户名或密码错误'
MSG_ERR_UNKNOWN = '登录失败，未知错误'
MSG_ERR_PARAM = '参数错误'
MSG_ONECARD_BIND_SUCCESS = '一卡通账号关联成功'
MSG_EXCEED_BMOB_BIND_TIMES_LIMIT = '您已经绑定过账号，请与我们联系处理'
MSG_EXCEED_ONECARD_BIND_TIMES_LIMIT = '该账号已被绑定，请与我们联系处理'
MSG_ONLINE_BANK_CHARGE_SUCCESS = '转账申请成功，到账可能会有延迟，请耐心等待！'
MSG_ONLINE_BANK_CHARGE_ERR_UNKNOWN = '未知错误'
MSG_ONLINE_BANK_CHARGE_INVALID_AMOUNT = '非法的充值金额，请重新输入！'
MSG_ONLINE_BANK_CHARGE_INVALID_AMOUNT_ZERO = '充值金额不能为0！'
MSG_ONLINE_BANK_CHARGE_PAY_PASSWORD_WRONG = '交易密码错误，请重新输入！'


def init(username, password, usertype='卡户'):
    session = Session(username, password, usertype)
    status, message = session.login()
    return session, status, message


def gen_header_base():
    return {
        'Accept': 'text/html, application/xhtml+xml, image/jxr, */*',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-Hans-CN,zh-Hans;q=0.8,en-US;q=0.5,en;q=0.3',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
    }


def gen_header_referer_is_logged_in(logged_in=False):
    header = gen_header_base()
    header.update({
        'Referer': URL_LOGIN if not logged_in else URL_MAIN,
        'Pragma': 'no-cache',
    })
    return header


def gen_header_referer_account_detail():
    header = gen_header_base()
    header.update({
        'Referer': URL_ACCOUNT_DETAIL,
    })
    return header


def gen_header_referer_online_bank():
    header = gen_header_base()
    header.update({
        'Referer': URL_ONLINE_BANK_CHARGE,
        'Pragma': 'no-cache',
    })
    return header


class Session(requests.Session):

    def __init__(self, username='', password='', usertype='卡户'):
        super().__init__()
        self.username = username
        self.password = password
        self.usertype = usertype
        # Result code represents session status
        self.result_code = 0

    def login(self):
        global result

        # Get and parse captcha
        html = self.get(URL_LOGIN, headers=gen_header_base())
        html.encoding = 'gbk'
        html_content = html.content.decode('gbk')

        # Post data
        __viewstate, __eventvalidation = self.parse_body_extras(html_content)
        captcha = self.parse_captcha(html_content)
        data = {
            '__VIEWSTATE': __viewstate,
            '__EVENTVALIDATION': __eventvalidation,
            'UserLogin:txtUser': self.username,
            'UserLogin:txtPwd': self.password,
            'UserLogin:ddlPerson': self.usertype.encode('gbk'),
            'UserLogin:txtSure': captcha,
            'UserLogin:ImageButton1.x': random.randint(0, 100),
            'UserLogin:ImageButton1.y': random.randint(0, 100),
        }

        # Perform login
        print('Perform login as username: ' + self.username + ', password: ' + self.password)
        result = self.post(URL_LOGIN, data=data, headers=gen_header_referer_is_logged_in())
        self.result_code = result.status_code
        result_content = result.content.decode('gbk')
        # Get the two body extras used for logout
        self.__viewstate, self.__eventvalidation = \
            self.parse_body_extras(result_content)
        status, message = self.check_status(result_content)
        return status, message

    def parse_body_extras(self, content):
        selector = etree.HTML(content)
        __viewstate = selector.xpath(r'//*[@name="__VIEWSTATE"]')
        __eventvalidation = selector.xpath(r'//*[@name="__EVENTVALIDATION"]')
        if __viewstate and __eventvalidation:
            return __viewstate[0].attrib['value'], __eventvalidation[0].attrib['value']

    def get_body_extras(self):
        return self.__viewstate, self.__eventvalidation

    def parse_captcha(self, content):
        selector = etree.HTML(content)
        arrs = selector.xpath(r'//*[@bgcolor="#d6cece"]//img')
        captcha = str()
        for each in arrs:
            captcha += re.search(r'(\d)', each.attrib['src'], re.S).group(0)
        return captcha

    def check_status(self, content):
        if self.result_code == 200:
            if content.find('学工号') != -1:
                # Login success!
                return STATUS_SUCCESS, MSG_SUCCESS
            else:
                return STATUS_LOGIN_FAILED, MSG_LOGIN_FAILED
        print('OneCard Login failed for unknown reason!')
        return STATUS_ERR_UNKNOWN, MSG_ERR_UNKNOWN

    def logout(self,):
        data = {
            '__VIEWSTATE': self.__viewstate,
            '__EVENTVALIDATION': self.__eventvalidation,
            'UserLogin:ImageButton1.x': random.randint(0, 100),
            'UserLogin:ImageButton1.y': random.randint(0, 100),
        }
        self.post(URL_MAIN, data=data, headers=gen_header_referer_is_logged_in(True))
        self.close()


class OneCardBase:

    def __init__(self, username, password=None):
        self.response_data = OrderedDict()
        if not password:
            password = self.__get_user_password(username)
        # Log in
        self.session, self.code, self.message = init(username, password)
        # Append status and message
        self.response_data['code'] = self.code
        self.response_data['message'] = self.message

    def __get_user_password(self, username):
        try:
            onecard_user = OneCardUser.objects.get(username=username)
            return onecard_user.password
        except OneCardUser.DoesNotExist:
            return None

    def _append_error_response_data(self, status, message):
        self.response_data['code'] = status
        self.response_data['message'] = message
        self.response_data['result'] = None


class OneCardAccountDetail(OneCardBase):

    def __init__(self, username, password=None):
        super().__init__(username, password)

    def get_detail(self):
        if self.code == STATUS_SUCCESS:
            detail_html = self.session.get(URL_ACCOUNT_DETAIL, headers=gen_header_referer_is_logged_in(True))
            if detail_html:
                self.parse(detail_html.content.decode('gbk'), True)
                # Log out
                self.session.logout()
        return self.response_data

    def parse(self, content, has_avatar=False):
        result = OrderedDict()
        selector = etree.HTML(content)
        result['personCode'] = selector.xpath(r'//*[@id="lblPerCode0"]/text()')[0]
        result['cardNumber'] = selector.xpath(r'//*[@id="lblCardNum0"]/text()')[0]
        result['account'] = selector.xpath(r'//*[@id="lblAcc0"]/text()')[0]
        result['role'] = selector.xpath(r'//*[@id="lblClsName0"]/text()')[0]
        result['name'] = selector.xpath(r'//*[@id="lblName0"]/text()')[0]
        result['sex'] = selector.xpath(r'//*[@id="lblSex0"]/text()')[0]
        result['department'] = selector.xpath(r'//*[@id="lblDep0"]/text()')[0]
        result['status'] = selector.xpath(r'//*[@id="lblAccStatus0"]/text()')[0]
        result['certType'] = selector.xpath(r'//*[@id="lblCertTypeNum0"]/text()')[0]
        result['certNumber'] = selector.xpath(r'//*[@id="lblCertCode0"]/text()')[0]
        result['expire'] = selector.xpath(r'//*[@id="lblLostDate0"]/text()')[0]
        result['cardType'] = selector.xpath(r'//*[@id="lblAccType0"]/text()')[0]
        # Get avatar
        if has_avatar:
            avatar_raw = self.session.get(
                URL_ACCOUNT_DETAIL_AVATAR + result.get('account'),
                headers=gen_header_referer_account_detail()
            )
            if avatar_raw:
                try:
                    result['avatar'] = base64.b64encode(bytes(avatar_raw.content)).decode('utf-8')
                except IOError as e:
                    result['avatar'] = None
                    print(e)
        else:
            result['avatar'] = None
        self.response_data['result'] = result


class OneCardBalance(OneCardBase):

    def __init__(self, username, password=None):
        super().__init__(username, password)

    def get_balance(self):
        if self.code == STATUS_SUCCESS:
            balance_html = self.session.get(URL_ACCOUNT_BALANCE, headers=gen_header_referer_is_logged_in(True))
            # Parse & extract the balance
            if balance_html:
                self.parse_balance(balance_html.content.decode('gbk'))
                # Log out
                self.session.logout()
        return self.response_data

    def parse_balance(self, content):
        result = OrderedDict()
        selector = etree.HTML(content)
        result['account'] = selector.xpath(r'//*[@id="lblPerCode0"]/text()')[0]
        result['name'] = selector.xpath(r'//*[@id="lblName0"]/text()')[0]
        result['cardNumber'] = selector.xpath(r'//*[@id="lblCardNum0"]/text()')[0]
        result['balance'] = selector.xpath(r'//*[@id="lblOne0"]/text()')[0]
        self.response_data['result'] = result

    def charge(self, amount, pay_password):
        if self.code == STATUS_SUCCESS:
            # Must the __VIEWSTATE and __EVENTVALIDATION first
            html = self.session.get(URL_ONLINE_BANK_CHARGE, headers=gen_header_referer_is_logged_in(True))
            __viewstate, __eventvalidation = self.parse_charge_extras(html.content.decode('gbk'))

            data = {
                '__VIEWSTATE': __viewstate,
                '__EVENTVALIDATION': __eventvalidation,
                'txtMonDeal': amount,
                'txtPayPwd': pay_password,
                'btnOk.x': random.randint(0, 100),
                'btnOk.y': random.randint(0, 100),
            }
            charge_result = self.session.post(URL_ONLINE_BANK_CHARGE, data=data,
                                              headers=gen_header_referer_online_bank())
            if charge_result:
                self.parse_charge(charge_result.content.decode('gbk'))
                # Log out
                self.session.logout()
                print('Finish online bank charge, amount: ' + amount)
        return self.response_data

    def parse_charge_extras(self, content):
        selector = etree.HTML(content)
        __viewstate = selector.xpath(r'//*[@name="__VIEWSTATE"]')
        __eventvalidation = selector.xpath(r'//*[@name="__EVENTVALIDATION"]')
        if __viewstate and __eventvalidation:
            return __viewstate[0].attrib['value'], __eventvalidation[0].attrib['value']

    def parse_charge(self, content):
        if content.find('转账申请成功') != -1:
            self.response_data['code'] = STATUS_SUCCESS
            self.response_data['message'] = MSG_ONLINE_BANK_CHARGE_SUCCESS
            self.response_data['result'] = {}
        elif content.find('充值金额非法') != -1:
            self._append_error_response_data(
                STATUS_ONLINE_BANK_CHARGE_INVALID_AMOUNT,
                MSG_ONLINE_BANK_CHARGE_INVALID_AMOUNT
            )
        elif content.find('请输入充值金额') != -1:
            self._append_error_response_data(
                STATUS_ONLINE_BANK_CHARGE_INVALID_AMOUNT,
                MSG_ONLINE_BANK_CHARGE_INVALID_AMOUNT_ZERO
            )
        elif content.find('密码错误，请重新输入') != -1:
            self._append_error_response_data(
                STATUS_ONLINE_BANK_CHARGE_PAY_PASSWORD_WRONG,
                MSG_ONLINE_BANK_CHARGE_PAY_PASSWORD_WRONG
            )
        else:
            self._append_error_response_data(
                STATUS_ONLINE_BANK_CHARGE_ERR_UNKNOWN,
                MSG_ONLINE_BANK_CHARGE_ERR_UNKNOWN
            )
