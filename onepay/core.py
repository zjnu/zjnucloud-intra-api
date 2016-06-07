from collections import OrderedDict
import random
import re
from django.utils.datastructures import MultiValueDictKeyError

from lxml import etree
import requests


# OnePay_URL
URL_LOGIN = 'http://ykt.zjnu.edu.cn/'
URL_MAIN = 'http://ykt.zjnu.edu.cn/Cardholder/Cardholder.aspx'
URL_ONLINE_BANK_CHARGE = 'http://ykt.zjnu.edu.cn/Cardholder/Onlinebank.aspx'
URL_ELECTRICITY_CHARGE = 'http://ykt.zjnu.edu.cn/Cardholder/SelfHelpElec.aspx'

# Session status code
STATUS_SUCCESS = 200
STATUS_LOGIN_FAILED = 403
STATUS_ERR_UNKNOWN = 101000
STATUS_ERR_PARAM = 101001
STATUS_EXCEED_BMOB_BIND_TIMES_LIMIT = 101002
STATUS_EXCEED_EMIS_BIND_TIMES_LIMIT = 101003

# Messages
MSG_SUCCESS = 'success'
MSG_LOGIN_FAILED = '登录失败，用户名或密码错误'
MSG_ERR_UNKNOWN = '登录失败，未知错误'
MSG_ERR_PARAM = '参数错误'
MSG_ONEPAY_BIND_SUCCESS = '一卡通账号关联成功'
MSG_EXCEED_BMOB_BIND_TIMES_LIMIT = '您已经绑定过账号，请与我们联系处理'
MSG_EXCEED_ONEPAY_BIND_TIMES_LIMIT = '该账号已被绑定，请与我们联系处理'


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


def gen_header_with_referer(logged_in=False):
    return gen_header_base().update({
        'Referer': URL_LOGIN if not logged_in else URL_MAIN,
        'Pragma': 'no-cache',
    })


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
        result = self.post(URL_LOGIN, data=data, headers=gen_header_with_referer())
        self.result_code = result.status_code
        result_content = result.content.decode('gbk')
        # Get the two body extras used for logout
        self.__viewstate_for_logout, self.__eventvalidation_for_logout = \
            self.parse_body_extras(result_content)
        status, message = self.check_status(result_content)
        return status, message

    def parse_body_extras(self, content):
        selector = etree.HTML(content)
        __viewstate = selector.xpath(r'//*[@name="__VIEWSTATE"]')
        __eventvalidation = selector.xpath(r'//*[@name="__EVENTVALIDATION"]')
        if __viewstate and __eventvalidation:
            return __viewstate[0].attrib['value'], __eventvalidation[0].attrib['value']

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
        print('OnePay Login failed for unknown reason!')
        return STATUS_ERR_UNKNOWN, MSG_ERR_UNKNOWN

    def logout(self,):
        data = {
            '__VIEWSTATE': self.__viewstate_for_logout,
            '__EVENTVALIDATION': self.__eventvalidation_for_logout,
            'UserLogin:ImageButton1.x': random.randint(0, 100),
            'UserLogin:ImageButton1.y': random.randint(0, 100),
        }
        self.post(URL_MAIN, data=data, headers=gen_header_with_referer(True))
        self.close()


class OnePayBase:

    def __init__(self, request):
        self.response_data = OrderedDict()
        try:
            if request is not None:
                # Detect request method
                if request.method == 'POST':
                    self.username = request.data['username']
                    self.password = request.data['password']
                # Log in
                self.session, self.code, self.message = init(self.username, self.password)
        except MultiValueDictKeyError:
            self.code = STATUS_ERR_PARAM
            self.message = MSG_ERR_PARAM
        # Append status and message
        self.response_data['code'] = self.code
        self.response_data['message'] = self.message


class OnlineBankCharge(OnePayBase):

    def __init__(self, request):
        super().__init__(request)

    def get_balance(self):
        if self.code == STATUS_SUCCESS:
            balance_html = self.session.get(URL_ONLINE_BANK_CHARGE, headers=gen_header_with_referer(True))
            # Parse & extract the balance
            if balance_html:
                selector = etree.HTML(balance_html.content.decode('gbk'))
                balance = selector.xpath(r'//*[@name="txtMon"]')[0].attrib['value']
                return balance
        return str()

    def do_charge(self):
        if self.code == STATUS_SUCCESS:
            print('Do online bank charge...')
