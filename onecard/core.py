from collections import OrderedDict
import random
import re
import base64
import decimal

from lxml import etree
import requests

from onecard.models import OneCardUser, OneCardCharge, OneCardElectricityRoom
from onecard.tasks import refresh_charge_status

# OneCard_URL
URL_LOGIN = 'http://ykt.zjnu.edu.cn/'
URL_MAIN = 'http://ykt.zjnu.edu.cn/Cardholder/Cardholder.aspx'
URL_DETAIL = 'http://ykt.zjnu.edu.cn/Cardholder/AccInfo.aspx'
URL_DETAIL_AVATAR = 'http://ykt.zjnu.edu.cn/Cardholder/ShowImage.aspx?AccNum='
URL_BALANCE = 'http://ykt.zjnu.edu.cn/Cardholder/AccBalance.aspx'
URL_DAILY_TRANSACTIONS = 'http://ykt.zjnu.edu.cn/Cardholder/QueryCurrDetailFrame.aspx'
URL_MONTHLY_TRANSACTIONS_DETAIL = 'http://ykt.zjnu.edu.cn/Cardholder/QueryhistoryDetail.aspx'
URL_MONTHLY_TRANSACTIONS_DETAIL_FRAME = 'http://ykt.zjnu.edu.cn/Cardholder/QueryhistoryDetailFrame.aspx'
URL_MONTHLY_TRANSACTIONS_POST = 'http://ykt.zjnu.edu.cn/Cardholder/Queryhistory.aspx'
URL_TRANSACTIONS_REFERER = 'http://ykt.zjnu.edu.cn/Cardholder/QueryCurrDetail.aspx'
URL_ONLINE_BANK_CHARGE = 'http://ykt.zjnu.edu.cn/Cardholder/Onlinebank.aspx'
URL_ELECTRICITY_GET_BUILDINGS = 'http://ykt.zjnu.edu.cn/Cardholder/SelfHelpElec.aspx'
URL_ELECTRICITY_PAY = 'http://ykt.zjnu.edu.cn/Cardholder/SelfHelpPay.aspx'

# Session status code
STATUS_SUCCESS = 200
STATUS_PAGE_NOT_AVAILABLE = 304
STATUS_LOGIN_FAILED = 403
STATUS_ERR_UNKNOWN = 101000
STATUS_ERR_PARAM = 101001
STATUS_EXCEED_BMOB_BIND_TIMES_LIMIT = 101002
STATUS_EXCEED_ONECARD_BIND_TIMES_LIMIT = 101003
STATUS_ONLINE_BANK_CHARGE_APPLIED = 101100
STATUS_ONLINE_BANK_CHARGE_INVALID_AMOUNT = 101101
STATUS_ONLINE_BANK_CHARGE_PAY_PASSWORD_WRONG = 101102
STATUS_ONLINE_BANK_CHARGE_AMOUNT_LIMIT = 101103
STATUS_ONLINE_BANK_CHARGE_ERR_UNKNOWN = 101199
STATUS_ELECTRICITY_BUILDING_NOT_FOUND = 101200
STATUS_ELECTRICITY_GET_ROOM_INFO_FAILED = 101201

# Messages
MSG_SUCCESS = 'success'
MSG_PAGE_NOT_AVAILABLE = '一卡通网站遇到了技术问题，暂时不可用'
MSG_LOGIN_FAILED = '登录失败，用户名或密码错误'
MSG_ERR_UNKNOWN = '登录失败，未知错误'
MSG_ERR_PARAM = '参数错误'
MSG_ONECARD_BIND_SUCCESS = '一卡通账号关联成功'
MSG_EXCEED_BMOB_BIND_TIMES_LIMIT = '您已经绑定过账号，请与我们联系处理'
MSG_EXCEED_ONECARD_BIND_TIMES_LIMIT = '该账号已被绑定，请与我们联系处理'
MSG_ONLINE_BANK_CHARGE_APPLIED = '转账申请成功，到账可能会有延迟，请耐心等待！'
MSG_ONLINE_BANK_CHARGE_SUCCESS = '一卡通充值已成功！充值金额为{}元'
MSG_ONLINE_BANK_CHARGE_ERR_UNKNOWN = '未知错误'
MSG_ONLINE_BANK_CHARGE_INVALID_AMOUNT = '非法的充值金额，请重新输入！'
MSG_ONLINE_BANK_CHARGE_INVALID_AMOUNT_ZERO = '充值金额必须大于0！'
MSG_ONLINE_BANK_CHARGE_PAY_PASSWORD_WRONG = '交易密码错误，请重新输入！'
MSG_ONLINE_BANK_CHARGE_BANK_BALANCE_INSUFFICIENT = '转账失败，请检查银行卡余额是否不足！'
MSG_ONLINE_BANK_CHARGE_AMOUNT_LIMIT = '由于安全原因，充值金额不得超过1000元！'
MSG_ELECTRICITY_BUILDINGS_CREATED = '所有楼房已获取'
MSG_ELECTRICITY_BUILDINGS_NOT_FOUND = '未找到对应房间号'
MSG_ELECTRICITY_GET_ROOM_INFO_FAILED = '未能获取房间电量信息'

# Results
# Unknown result code
RESULT_CODE_ONLINE_BANK_CHARGE_UNKNOWN = -1
# Stands for charge in process
RESULT_CODE_ONLINE_BANK_CHARGE_TRANSFER_IN_PROCESS = 0
# Stands for charge complete successfully
RESULT_CODE_ONLINE_BANK_CHARGE_TRANSFER_SUCCESS = 1
# Stands for insufficient amount in bank account
RESULT_CODE_ONLINE_BANK_CHARGE_BANK_BALANCE_INSUFFICIENT = 2

# Limits
ONECARD_USER_LIMIT = 1
ONECARD_CHARGE_AMOUNT_LIMIT = 1000000


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
        'Referer': URL_DETAIL,
    })
    return header


def gen_header_referer_online_bank():
    header = gen_header_base()
    header.update({
        'Referer': URL_ONLINE_BANK_CHARGE,
        'Pragma': 'no-cache',
    })
    return header


def gen_header_referer_daily_transactions():
    header = gen_header_base()
    header.update({
        'Referer': URL_TRANSACTIONS_REFERER,
    })
    return header


def gen_header_referer_monthly_transactions_post_params():
    header = gen_header_base()
    header.update({
        'Referer': URL_MONTHLY_TRANSACTIONS_POST,
        'Pragma': 'no-cache',
    })
    return header


def gen_header_referer_monthly_transactions_get():
    header = gen_header_base()
    header.update({
        'Referer': URL_TRANSACTIONS_REFERER,
    })
    return header


def gen_header_referer_electricity():
    header = gen_header_base()
    header.update({
        'Accept': 'image/gif, image/jpeg, image/pjpeg, application/x-ms-application, '
                  'application/xaml+xml, application/x-ms-xbap, */*',
        'Referer': URL_ELECTRICITY_GET_BUILDINGS,
        'Pragma': 'no-cache',
    })
    return header


def get_response_data_without_result(code='404', message=''):
    data = OrderedDict()
    data['code'] = code
    data['message'] = message
    data['result'] = None
    return data


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
        status, message = self.check_status(html_content, False)
        if status != STATUS_SUCCESS:
            return status, message

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
        print('OneCard login as username: ' + self.username + ', password: ' + self.password)
        result = self.post(URL_LOGIN, data=data, headers=gen_header_referer_is_logged_in())
        self.result_code = result.status_code
        result_content = result.content.decode('gbk')
        # Get the two body extras used for logout
        self.__viewstate, self.__eventvalidation = \
            self.parse_body_extras(result_content)
        status, message = self.check_status(result_content)
        return status, message

    @staticmethod
    def parse_body_extras(content):
        selector = etree.HTML(content)
        __viewstate = selector.xpath(r'//*[@name="__VIEWSTATE"]')
        __eventvalidation = selector.xpath(r'//*[@name="__EVENTVALIDATION"]')
        if __viewstate and __eventvalidation:
            return __viewstate[0].attrib['value'], __eventvalidation[0].attrib['value']
        elif __viewstate:
            return __viewstate[0].attrib['value']
        elif __eventvalidation:
            return __eventvalidation[0].attrib['value']
        else:
            return None

    def get_body_extras(self):
        return self.__viewstate, self.__eventvalidation

    def parse_captcha(self, content):
        selector = etree.HTML(content)
        arrs = selector.xpath(r'//*[@bgcolor="#d6cece"]//img')
        captcha = str()
        for each in arrs:
            captcha += re.search(r'(\d)', each.attrib['src'], re.S).group(0)
        return captcha

    def check_status(self, content, is_login=True):
        """
        Check web page status by parsing the response content
        """

        if is_login and self.result_code == 200:
            if content.find('学工号') != -1:
                # Login success!
                return STATUS_SUCCESS, MSG_SUCCESS
            else:
                return STATUS_LOGIN_FAILED, MSG_LOGIN_FAILED
        else:
            if content.find('登录号') != -1:
                return STATUS_SUCCESS, MSG_SUCCESS
            elif content.find('您要查看的页当前不可用。找不到服务器或网站遇到技术问题。') != -1:
                return STATUS_PAGE_NOT_AVAILABLE, MSG_PAGE_NOT_AVAILABLE
            else:
                return STATUS_ERR_UNKNOWN, MSG_ERR_UNKNOWN

    def logout(self, ):
        data = {
            '__VIEWSTATE': self.__viewstate,
            '__EVENTVALIDATION': self.__eventvalidation,
            'UserLogin:ImageButton1.x': random.randint(0, 100),
            'UserLogin:ImageButton1.y': random.randint(0, 100),
        }
        self.post(URL_MAIN, data=data, headers=gen_header_referer_is_logged_in(True))
        self.close()


class OneCardBase:
    def __init__(self, username=None, password=None):
        if username:
            self.response_data = OrderedDict()
            if not password:
                password = self.__get_user_password(username)
            # Log in
            self.session, self.code, self.message = self.init(username, password)
            # Append status and message
            self.response_data['code'] = self.code
            self.response_data['message'] = self.message
            self.response_data['result'] = None

    @staticmethod
    def init(username, password, usertype='卡户'):
        session = Session(username, password, usertype)
        status, message = session.login()
        return session, status, message

    @staticmethod
    def __get_user_password(username):
        try:
            onecard_user = OneCardUser.objects.get(username=username)
            return onecard_user.password
        except OneCardUser.DoesNotExist:
            return None

    def _append_error_response_data(self, code, message):
        self.response_data['code'] = code
        self.response_data['message'] = message
        self.response_data['result'] = None


class OneCardAccountDetail(OneCardBase):
    def get_detail(self):
        if self.code == STATUS_SUCCESS:
            detail_html = self.session.get(URL_DETAIL, headers=gen_header_referer_is_logged_in(True))
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
                URL_DETAIL_AVATAR + result.get('account'),
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
    def __init__(self, username=None, password=None):
        super().__init__(username, password)
        self.username = username
        self.password = password

    def get_balance(self):
        if self.code == STATUS_SUCCESS:
            balance_html = self.session.get(URL_BALANCE, headers=gen_header_referer_is_logged_in(True))
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

    def charge(self, amount, pay_password, push_credential=None):
        if self.code == STATUS_SUCCESS:
            # Must get __VIEWSTATE and __EVENTVALIDATION first
            html = self.session.get(URL_ONLINE_BANK_CHARGE, headers=gen_header_referer_is_logged_in(True))
            __viewstate, __eventvalidation = Session.parse_body_extras(html.content.decode('gbk'))
            self.amount = amount
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
                content = charge_result.content.decode('gbk')
                self.parse_charge(content)

                # Save charge
                self.response_data['username'] = self.username
                self.response_data['amount'] = amount
                charge_object = OneCardCharge.objects.create(
                    code=self.response_data.get('code'),
                    message=self.response_data.get('message'),
                    result=self.response_data.get('result'),
                    user=OneCardUser.objects.get(username=self.response_data.get('username')),
                    amount=self.response_data.get('amount'),
                )

                # Refresh charge status in celery task if push_credential provided
                if push_credential:
                    __viewstate_refresh, __eventvalidation_refresh = Session.parse_body_extras(content)
                    data = {
                        '__VIEWSTATE': __viewstate_refresh,
                        '__EVENTVALIDATION': __eventvalidation_refresh,
                        '__EVENTTARGET': 'LinkButton1',
                        '__EVENTARGUMENT': '',
                        'txtMonDeal': '',
                        'txtPayPwd': '',
                        '__smartNavPostBack': 'true',
                    }
                    charge_object_id = charge_object.pk
                    refresh_charge_status.delay(self.session, self.username, self.amount,
                                                data, charge_object_id, push_credential)

        return self.response_data

    @staticmethod
    def check_amount(amount):
        """
        Check and validate the charge amount
        :param amount: in str, float or decimal
        :return: Boolean, Number
        """
        try:
            n = round(decimal.Decimal(amount.strip()), 2)
            if n < ONECARD_CHARGE_AMOUNT_LIMIT:
                return True, n
            else:
                return False, n
        except Exception as e:
            print(e)
        return False, None

    def parse_charge(self, content):
        if content.find('转账申请成功') != -1:
            self.response_data['code'] = STATUS_ONLINE_BANK_CHARGE_APPLIED
            self.response_data['message'] = MSG_ONLINE_BANK_CHARGE_APPLIED
            self.response_data['result'] = RESULT_CODE_ONLINE_BANK_CHARGE_TRANSFER_IN_PROCESS
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
        elif content.find('缴费金额必须大于0') != -1:
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


class OneCardTransactions(OneCardBase):
    def get_daily(self):
        if self.code == STATUS_SUCCESS:
            content_html = self.session.get(URL_DAILY_TRANSACTIONS,
                                            headers=gen_header_referer_daily_transactions())
            # Parse & extract the balance
            if content_html:
                self.parse_all_data(content_html.content.decode('gbk'))
                # Log out
                self.session.logout()
        return self.response_data

    def get_monthly(self, year, month):
        if self.code == STATUS_SUCCESS:
            # Must get __VIEWSTATE first
            content_html = self.session.get(URL_MONTHLY_TRANSACTIONS_POST,
                                            headers=gen_header_referer_monthly_transactions_get())
            __viewstate = Session.parse_body_extras(content_html.content.decode('gbk'))
            data = {
                '__VIEWSTATE': __viewstate,
                'ddlYear': year,
                'ddlMonth': month,
                'txtMonth': month,
                'ImageButton1.x': random.randint(0, 100),
                'ImageButton1.y': random.randint(0, 100),
            }
            self.session.post(URL_MONTHLY_TRANSACTIONS_POST,
                              data=data,
                              headers=gen_header_referer_monthly_transactions_post_params())

            content_html = self.session.get(URL_MONTHLY_TRANSACTIONS_DETAIL_FRAME, headers=gen_header_base())

            # Parse & extract the balance
            if content_html:
                self.parse_all_data(content_html.content.decode('gbk'))
                # Log out
                self.session.logout()
        return self.response_data

    def parse_all_data(self, content):
        if content.find('没有检索到符合的记录') != -1:
            self.response_data['result'] = {}
        elif content.find('交易记录') != -1:
            result = list()
            selector = etree.HTML(content)
            records = selector.xpath(r'//table/tr')
            for record in records[-4:3:-1]:
                fields = record.xpath(r'td/text()')
                result.append(self.append_transaction(fields))
            self.response_data['result'] = result

    @staticmethod
    def append_transaction(fields):
        transaction_data = OrderedDict()
        transaction_data['transactionId'] = str(fields[0])
        transaction_data['account'] = str(fields[1])
        transaction_data['cardType'] = str(fields[2])
        transaction_data['transactionType'] = str(fields[3])
        transaction_data['businessName'] = str(fields[4])
        transaction_data['businessSite'] = str(fields[5])
        transaction_data['terminalNo'] = str(fields[6])
        transaction_data['amount'] = str(fields[7])
        transaction_data['date'] = str(fields[8])
        transaction_data['walletName'] = str(fields[9])
        transaction_data['balance'] = str(fields[10])
        return transaction_data


class OneCardElectricity(OneCardBase):
    def get_and_save_buildings(self):
        res = self.session.get(URL_ELECTRICITY_GET_BUILDINGS, headers=gen_header_base())
        content = res.content.decode('gbk')
        # Get __VIEWSTATE, __EVENTVALIDATION
        __viewstate, __eventvalidation = Session.parse_body_extras(content)

        selector = etree.HTML(content)
        buildings = selector.xpath(r'//select[@name="lsArea"]/option/text()')

        # Bulk create if no data in the table to improve performance
        is_empty_table = True if not OneCardElectricityRoom.objects.all() else False
        if is_empty_table:
            room_objects = list()

        for index, building in enumerate(buildings):
            data = {
                'lsArea': building.encode('gbk'),
                '__VIEWSTATE': __viewstate,
                '__EVENTVALIDATION': __eventvalidation,
                '__EVENTTARGET': 'lsArea',
                '__smartNavPostBack': 'true',
                '__EVENTARGUMENT': '',
                '__LASTFOCUS': '',
            }
            res = self.session.post(URL_ELECTRICITY_GET_BUILDINGS,
                                    headers=gen_header_referer_electricity(),
                                    data=data)
            content = res.content.decode('gbk')
            # Save these for next request
            __viewstate, __eventvalidation = Session.parse_body_extras(content)

            selector = etree.HTML(content)
            rooms = selector.xpath(r'//select[@name="lsRoom"]/option')

            for room in rooms:
                value = room.attrib['value']
                text = room.text
                if is_empty_table:
                    room_objects.append(OneCardElectricityRoom(building=building, room=text, value=value))
                else:
                    OneCardElectricityRoom.objects.get_or_create(building=building, room=text, value=value)

        # Do bulk_create
        if is_empty_table:
            OneCardElectricityRoom.objects.bulk_create(room_objects)

        self.response_data['message'] = MSG_ELECTRICITY_BUILDINGS_CREATED
        self.response_data['result'] = None
        return self.response_data

    def get_and_save_extras(self):
        # TODO
        pass

    def get_room_info(self, building, room):
        try:
            _room = OneCardElectricityRoom.objects.filter(building='初阳', room='A1-104')[0]
            if not self.__post_room_data(_room):
                self.response_data['code'] = STATUS_SUCCESS
                self.response_data['message'] = MSG_ELECTRICITY_GET_ROOM_INFO_FAILED
                return self.response_data

            res = self.session.get(URL_ELECTRICITY_PAY, headers=gen_header_referer_electricity())
            content = res.content.decode('gbk')
            self.parse_room_info(content)

        except OneCardElectricityRoom.DoesNotExist:
            self._append_error_response_data(
                STATUS_ELECTRICITY_BUILDING_NOT_FOUND,
                MSG_ELECTRICITY_BUILDINGS_NOT_FOUND
            )
        return self.response_data

    def parse_room_info(self, content):
        selector = etree.HTML(content)
        result = OrderedDict()
        result['balance'] = selector.xpath(r'//*[@id="lblItem"]/text()')
        self.response_data[result] = result

    def __post_room_data(self, room_object):
        # Get __VIEWSTATE and __EVENTVALIDATION first
        __viewstate = r'/wEPDwULLTE4NDAzNDI0MjYPZBYCAgEPZBYEAgsPEA8WBh4NRGF0YVRleHRGaWVsZAUIc2hvd25hbWUeDkRhdGFWYWx1ZUZpZWxkBQhzaG93bmFtZR4LXyFEYXRhQm91bmRnZBAVFgbliJ3pmLMG5qGC6IuRBuW8gOaUvgfmjqfliLYxCOaOp+WItjEwCOaOp+WItjExCOaOp+WItjEyCOaOp+WItjEzCOaOp+WItjE0COaOp+WItjE1COaOp+WItjE2B+aOp+WItjIH5o6n5Yi2MwfmjqfliLY0B+aOp+WItjUH5o6n5Yi2NgfmjqfliLY3B+aOp+WItjgH5o6n5Yi2OQblkK/mmI4G5qGD5rqQBuadj+WbrRUWBuWInemYswbmoYLoi5EG5byA5pS+B+aOp+WItjEI5o6n5Yi2MTAI5o6n5Yi2MTEI5o6n5Yi2MTII5o6n5Yi2MTMI5o6n5Yi2MTQI5o6n5Yi2MTUI5o6n5Yi2MTYH5o6n5Yi2MgfmjqfliLYzB+aOp+WItjQH5o6n5Yi2NQfmjqfliLY2B+aOp+WItjcH5o6n5Yi2OAfmjqfliLY5BuWQr+aYjgbmoYPmupAG5p2P5ZutFCsDFmdnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2cWAWZkAg0PEA8WBh8ABQhzaG93bmFtZR8BBQdyb29tX2lkHwJnZBAVgAkGQTEtMTE2BkExLTExNQZBMS0xMTQGQTEtMTEzBkExLTExMgZBMS0xMTEGQTEtMTEwBkExLTEwOQZBMS0xMDgGQTEtMTA3BkExLTEwNgZBMS0xMDUGQTEtMTA0BkExLTEwMwZBMS0xMDIGQTEtMTAxBkExLTIxNgZBMS0yMTUGQTEtMjE0BkExLTIxMwZBMS0yMTIGQTEtMjExBkExLTIxMAZBMS0yMDkGQTEtMjA4BkExLTIwNwZBMS0yMDYGQTEtMjA1BkExLTIwNAZBMS0yMDMGQTEtMjAyBkExLTIwMQZBMS0zMTYGQTEtMzE1BkExLTMxNAZBMS0zMTMGQTEtMzEyBkExLTMxMQZBMS0zMTAGQTEtMzA5BkExLTMwOAZBMS0zMDcGQTEtMzA2BkExLTMwNQZBMS0zMDQGQTEtMzAzBkExLTMwMgZBMS0zMDEGQTEtNDE2BkExLTQxNQZBMS00MTQGQTEtNDEzBkExLTQxMgZBMS00MTEGQTEtNDEwBkExLTQwOQZBMS00MDgGQTEtNDA3BkExLTQwNgZBMS00MDUGQTEtNDA0BkExLTQwMwZBMS00MDIGQTEtNDAxBkExLTUxNgZBMS01MTUGQTEtNTE0BkExLTUxMwZBMS01MTIGQTEtNTExBkExLTUxMAZBMS01MDkGQTEtNTA4BkExLTUwNwZBMS01MDYGQTEtNTA1BkExLTUwNAZBMS01MDMGQTEtNTAyBkExLTUwMQZBMS02MTYGQTEtNjE1BkExLTYxNAZBMS02MTMGQTEtNjEyBkExLTYxMQZBMS02MTAGQTEtNjA5BkExLTYwOAZBMS02MDcGQTEtNjA2BkExLTYwNQZBMS02MDQGQTEtNjAzBkExLTYwMgZBMS02MDEGQTItMTAxBkEyLTEwMgZBMi0xMDMGQTItMTA0BkEyLTEwNQZBMi0xMDYGQTItMTA3BkEyLTEwOAZBMi0xMDkGQTItMTEwBkEyLTExMQZBMi0xMTIGQTItMTEzBkEyLTIwMQZBMi0yMDIGQTItMjAzBkEyLTIwNAZBMi0yMDUGQTItMjA2BkEyLTIwNwZBMi0yMDgGQTItMjA5BkEyLTIxMAZBMi0yMTEGQTItMjEyBkEyLTIxMwZBMi0zMDEGQTItMzAyBkEyLTMwMwZBMi0zMDQGQTItMzA1BkEyLTMwNgZBMi0zMDcGQTItMzA4BkEyLTMwOQZBMi0zMTAGQTItMzExBkEyLTMxMgZBMi0zMTMGQTItMzE0BkEyLTMxNQZBMi00MDEGQTItNDAyBkEyLTQwMwZBMi00MDQGQTItNDA1BkEyLTQwNgZBMi00MDcGQTItNDA4BkEyLTQwOQZBMi00MTAGQTItNDExBkEyLTQxMgZBMi00MTMGQTItNTAxBkEyLTUwMgZBMi01MDMGQTItNTA0BkEyLTUwNQZBMi01MDYGQTItNTA3BkEyLTUwOAZBMi01MDkGQTItNTEwBkEyLTUxMQZBMi01MTIGQTItNTEzBkEyLTUxNAZBMi01MTUGQTItNjAxBkEyLTYwMgZBMi02MDMGQTItNjA0BkEyLTYwNQZBMi02MDYGQTItNjA3BkEyLTYwOAZBMi02MDkGQTItNjEwBkEyLTYxMQZBMi02MTIGQTItNjEzBkEyLTYxNAZBMi02MTUGQTMtMTAxBkEzLTEwMgZBMy0xMDMGQTMtMTA0BkEzLTEwNQZBMy0xMDYGQTMtMTA3BkEzLTIwMQZBMy0yMDIGQTMtMjAzBkEzLTIwNAZBMy0yMDUGQTMtMjA2BkEzLTIwNwZBMi00MTQGQTItNDE1BkIxLTExNQZCMS0xMTQGQjEtMTEzBkIxLTExMgZCMS0xMTEGQjEtMTEwBkIxLTEwOQZCMS0xMDgGQjEtMTA3BkIxLTEwNgZCMS0xMDUGQjEtMTA0BkIxLTEwMwZCMS0xMDIGQjEtMTAxBkIxLTIxNQZCMS0yMTQGQjEtMjEzBkIxLTIxMgZCMS0yMTEGQjEtMjEwBkIxLTIwOQZCMS0yMDgGQjEtMjA3BkIxLTIwNgZCMS0yMDUGQjEtMjA0BkIxLTIwMwZCMS0yMDIGQjEtMjAxBkIxLTMxNQZCMS0zMTQGQjEtMzEzBkIxLTMxMgZCMS0zMTEGQjEtMzEwBkIxLTMwOQZCMS0zMDgGQjEtMzA3BkIxLTMwNgZCMS0zMDUGQjEtMzA0BkIxLTMwMwZCMS0zMDIGQjEtMzAxBkIxLTQxNQZCMS00MTQGQjEtNDEzBkIxLTQxMgZCMS00MTEGQjEtNDEwBkIxLTQwOQZCMS00MDgGQjEtNDA3BkIxLTQwNgZCMS00MDUGQjEtNDA0BkIxLTQwMwZCMS00MDIGQjEtNDAxBkIxLTUxNQZCMS01MTQGQjEtNTEzBkIxLTUxMgZCMS01MTEGQjEtNTEwBkIxLTUwOQZCMS01MDgGQjEtNTA3BkIxLTUwNgZCMS01MDUGQjEtNTA0BkIxLTUwMwZCMS01MDIGQjEtNTAxBkIxLTYxNQZCMS02MTQGQjEtNjEzBkIxLTYxMgZCMS02MTEGQjEtNjEwBkIxLTYwOQZCMS02MDgGQjEtNjA3BkIxLTYwNgZCMS02MDUGQjEtNjA0BkIxLTYwMwZCMS02MDIGQjEtNjAxBkIyLTExMgZCMi0xMTEGQjItMTEwBkIyLTEwOQZCMi0xMDgGQjItMTA3BkIyLTEwNgZCMi0xMDUGQjItMTA0BkIyLTEwMwZCMi0xMDIGQjItMTAxBkIyLTIxMgZCMi0yMTEGQjItMjEwBkIyLTIwOQZCMi0yMDgGQjItMjA3BkIyLTIwNgZCMi0yMDUGQjItMjA0BkIyLTIwMwZCMi0yMDIGQjItMjAxBkIyLTMxNQZCMi0zMTQGQjItMzEzBkIyLTMxMgZCMi0zMTEGQjItMzEwBkIyLTMwOQZCMi0zMDgGQjItMzA3BkIyLTMwNgZCMi0zMDUGQjItMzA0BkIyLTMwMwZCMi0zMDIGQjItMzAxBkIyLTQxNQZCMi00MTQGQjItNDEzBkIyLTQxMgZCMi00MTEGQjItNDEwBkIyLTQwOQZCMi00MDgGQjItNDA3BkIyLTQwNgZCMi00MDUGQjItNDA0BkIyLTQwMwZCMi00MDIGQjItNDAxBkIyLTUxNQZCMi01MTQGQjItNTEzBkIyLTUxMgZCMi01MTEGQjItNTEwBkIyLTUwOQZCMi01MDgGQjItNTA3BkIyLTUwNgZCMi01MDUGQjItNTA0BkIyLTUwMwZCMi01MDIGQjItNTAxBkIyLTYxNQZCMi02MTQGQjItNjEzBkIyLTYxMgZCMi02MTEGQjItNjEwBkIyLTYwOQZCMi02MDgGQjItNjA3BkIyLTYwNgZCMi02MDUGQjItNjA0BkIyLTYwMwZCMi02MDIGQjItNjAxBkIzLTEwMQZCMy0xMDIGQjMtMTAzBkIzLTEwNAZCMy0xMDUGQjMtMTA2BkIzLTEwNwZCMy0yMDEGQjMtMjAyBkIzLTIwMwZCMy0yMDQGQjMtMjA1BkIzLTIwNgZCMy0yMDcGQzEtMTE2BkMxLTExNQZDMS0xMTQGQzEtMTEzBkMxLTExMgZDMS0xMTEGQzEtMTEwBkMxLTEwOQZDMS0xMDgGQzEtMTA3BkMxLTEwNgZDMS0xMDUGQzEtMTA0BkMxLTEwMwZDMS0xMDIGQzEtMTAxBkMxLTIxNgZDMS0yMTUGQzEtMjE0BkMxLTIxMwZDMS0yMTIGQzEtMjExBkMxLTIxMAZDMS0yMDkGQzEtMjA4BkMxLTIwNwZDMS0yMDYGQzEtMjA1BkMxLTIwNAZDMS0yMDMGQzEtMjAyBkMxLTIwMQZDMS0zMTYGQzEtMzE1BkMxLTMxNAZDMS0zMTMGQzEtMzEyBkMxLTMxMQZDMS0zMTAGQzEtMzA5BkMxLTMwOAZDMS0zMDcGQzEtMzA2BkMxLTMwNQZDMS0zMDQGQzEtMzAzBkMxLTMwMgZDMS0zMDEGQzEtNDE2BkMxLTQxNQZDMS00MTQGQzEtNDEzBkMxLTQxMgZDMS00MTEGQzEtNDEwBkMxLTQwOQZDMS00MDgGQzEtNDA3BkMxLTQwNgZDMS00MDUGQzEtNDA0BkMxLTQwMwZDMS00MDIGQzEtNDAxBkMxLTUxNgZDMS01MTUGQzEtNTE0BkMxLTUxMwZDMS01MTIGQzEtNTExBkMxLTUxMAZDMS01MDkGQzEtNTA4BkMxLTUwNwZDMS01MDYGQzEtNTA1BkMxLTUwNAZDMS01MDMGQzEtNTAyBkMxLTUwMQZDMS02MTYGQzEtNjE1BkMxLTYxNAZDMS02MTMGQzEtNjEyBkMxLTYxMQZDMS02MTAGQzEtNjA5BkMxLTYwOAZDMS02MDcGQzEtNjA2BkMxLTYwNQZDMS02MDQGQzEtNjAzBkMxLTYwMgZDMS02MDEGQzItMTAxBkMyLTEwMgZDMi0xMDMGQzItMTA0BkMyLTEwNQZDMi0xMDYGQzItMTA3BkMyLTEwOAZDMi0xMDkGQzItMTEwBkMyLTExMQZDMi0xMTIGQzItMTEzBkMyLTIwMQZDMi0yMDIGQzItMjAzBkMyLTIwNAZDMi0yMDUGQzItMjA2BkMyLTIwNwZDMi0yMDgGQzItMjA5BkMyLTIxMAZDMi0yMTEGQzItMjEyBkMyLTIxMwZDMi0zMDEGQzItMzAyBkMyLTMwMwZDMi0zMDQGQzItMzA1BkMyLTMwNgZDMi0zMDcGQzItMzA4BkMyLTMwOQZDMi0zMTAGQzItMzExBkMyLTMxMgZDMi0zMTMGQzItMzE0BkMyLTMxNQZDMi00MDEGQzItNDAyBkMyLTQwMwZDMi00MDQGQzItNDA1BkMyLTQwNgZDMi00MDcGQzItNDA4BkMyLTQwOQZDMi00MTAGQzItNDExBkMyLTQxMgZDMi00MTMGQzItNDE0BkMyLTQxNQZDMi01MDEGQzItNTAyBkMyLTUwMwZDMi01MDQGQzItNTA1BkMyLTUwNgZDMi01MDcGQzItNTA4BkMyLTUwOQZDMi01MTAGQzItNTExBkMyLTUxMgZDMi01MTMGQzItNTE0BkMyLTUxNQZDMi02MDEGQzItNjAyBkMyLTYwMwZDMi02MDQGQzItNjA1BkMyLTYwNgZDMi02MDcGQzItNjA4BkMyLTYwOQZDMi02MTAGQzItNjExBkMyLTYxMgZDMi02MTMGQzItNjE0BkMyLTYxNQZDMy0xMDEGQzMtMTAyBkMzLTEwMwZDMy0xMDQGQzMtMTA1BkMzLTEwNgZDMy0xMDcGQzMtMjAxBkMzLTIwMgZDMy0yMDMGQzMtMjA0BkMzLTIwNQZDMy0yMDYGQzMtMjA3BkQxLTExNQZEMS0xMTQGRDEtMTEzBkQxLTExMgZEMS0xMTEGRDEtMTEwBkQxLTEwOQZEMS0xMDgGRDEtMTA3BkQxLTEwNgZEMS0xMDUGRDEtMTA0BkQxLTEwMwZEMS0xMDIGRDEtMTAxBkQxLTIxNQZEMS0yMTQGRDEtMjEzBkQxLTIxMgZEMS0yMTEGRDEtMjEwBkQxLTIwOQZEMS0yMDgGRDEtMjA3BkQxLTIwNgZEMS0yMDUGRDEtMjA0BkQxLTIwMwZEMS0yMDIGRDEtMjAxBkQxLTMxNQZEMS0zMTQGRDEtMzEzBkQxLTMxMgZEMS0zMTEGRDEtMzEwBkQxLTMwOQZEMS0zMDgGRDEtMzA3BkQxLTMwNgZEMS0zMDUGRDEtMzA0BkQxLTMwMwZEMS0zMDIGRDEtMzAxBkQxLTQxNQZEMS00MTQGRDEtNDEzBkQxLTQxMgZEMS00MTEGRDEtNDEwBkQxLTQwOQZEMS00MDgGRDEtNDA3BkQxLTQwNgZEMS00MDUGRDEtNDA0BkQxLTQwMwZEMS00MDIGRDEtNDAxBkQxLTUxNQZEMS01MTQGRDEtNTEzBkQxLTUxMgZEMS01MTEGRDEtNTEwBkQxLTUwOQZEMS01MDgGRDEtNTA3BkQxLTUwNgZEMS01MDUGRDEtNTA0BkQxLTUwMwZEMS01MDIGRDEtNTAxBkQxLTYxNQZEMS02MTQGRDEtNjEzBkQxLTYxMgZEMS02MTEGRDEtNjEwBkQxLTYwOQZEMS02MDgGRDEtNjA3BkQxLTYwNgZEMS02MDUGRDEtNjA0BkQxLTYwMwZEMS02MDIGRDEtNjAxBkQyLTYxNQZEMi02MTQGRDItNjEzBkQyLTYxMgZEMi02MTEGRDItNjEwBkQyLTYwOQZEMi02MDgGRDItNjA3BkQyLTYwNgZEMi02MDUGRDItNjA0BkQyLTYwMwZEMi02MDIGRDItNjAxBkQyLTUxNQZEMi01MTQGRDItNTEzBkQyLTUxMgZEMi01MTEGRDItNTEwBkQyLTUwOQZEMi01MDgGRDItNTA3BkQyLTUwNgZEMi01MDUGRDItNTA0BkQyLTUwMwZEMi01MDIGRDItNTAxBkQyLTQxNQZEMi00MTQGRDItNDEzBkQyLTQxMgZEMi00MTEGRDItNDEwBkQyLTQwOQZEMi00MDgGRDItNDA3BkQyLTQwNgZEMi00MDUGRDItNDA0BkQyLTQwMwZEMi00MDIGRDItNDAxBkQyLTMxNQZEMi0zMTQGRDItMzEzBkQyLTMxMgZEMi0zMTEGRDItMzEwBkQyLTMwOQZEMi0zMDgGRDItMzA3BkQyLTMwNgZEMi0zMDUGRDItMzA0BkQyLTMwMwZEMi0zMDIGRDItMzAxBkQyLTIxMgZEMi0yMTEGRDItMjEwBkQyLTIwOQZEMi0yMDgGRDItMjA3BkQyLTIwNgZEMi0yMDUGRDItMjA0BkQyLTIwMwZEMi0yMDIGRDItMjAxBkQyLTExMgZEMi0xMTEGRDItMTEwBkQyLTEwOQZEMi0xMDgGRDItMTA3BkQyLTEwNgZEMi0xMDUGRDItMTA0BkQyLTEwMwZEMi0xMDIGRDItMTAxBkQzLTEwMQZEMy0xMDIGRDMtMTAzBkQzLTEwNAZEMy0xMDUGRDMtMTA2BkQzLTEwNwZEMy0yMDEGRDMtMjAyBkQzLTIwMwZEMy0yMDQGRDMtMjA1BkQzLTIwNgZEMy0yMDcGRTEtMTAxBkUxLTEwMgZFMS0xMDMGRTEtMTA0BkUxLTEwNQZFMS0xMDYGRTEtMTA3BkUxLTEwOAZFMS0xMDkGRTEtMTEwBkUxLTExMQZFMS0xMTIGRTEtMTEzBkUxLTExNAZFMS0xMTUGRTEtMTE2BkUxLTIwMQZFMS0yMDIGRTEtMjAzBkUxLTIwNAZFMS0yMDUGRTEtMjA2BkUxLTIwNwZFMS0yMDgGRTEtMjA5BkUxLTIxMAZFMS0yMTEGRTEtMjEyBkUxLTIxMwZFMS0yMTQGRTEtMjE1BkUxLTIxNgZFMS0zMDEGRTEtMzAyBkUxLTMwMwZFMS0zMDQGRTEtMzA1BkUxLTMwNgZFMS0zMDcGRTEtMzA4BkUxLTMwOQZFMS0zMTAGRTEtMzExBkUxLTMxMgZFMS0zMTMGRTEtMzE0BkUxLTMxNQZFMS0zMTYGRTEtNDAxBkUxLTQwMgZFMS00MDMGRTEtNDA0BkUxLTQwNQZFMS00MDYGRTEtNDA3BkUxLTQwOAZFMS00MDkGRTEtNDEwBkUxLTQxMQZFMS00MTIGRTEtNDEzBkUxLTQxNAZFMS00MTUGRTEtNDE2BkUxLTUwMQZFMS01MDIGRTEtNTAzBkUxLTUwNAZFMS01MDUGRTEtNTA2BkUxLTUwNwZFMS01MDgGRTEtNTA5BkUxLTUxMAZFMS01MTEGRTEtNTEyBkUxLTUxMwZFMS01MTQGRTEtNTE1BkUxLTUxNgZFMS02MDEGRTEtNjAyBkUxLTYwMwZFMS02MDQGRTEtNjA1BkUxLTYwNgZFMS02MDcGRTEtNjA4BkUxLTYwOQZFMS02MTAGRTEtNjExBkUxLTYxMgZFMS02MTMGRTEtNjE0BkUxLTYxNQZFMS02MTYGRTItMTAxBkUyLTEwMgZFMi0xMDMGRTItMTA0BkUyLTEwNQZFMi0xMDYGRTItMTA3BkUyLTEwOAZFMi0xMDkGRTItMTEwBkUyLTExMQZFMi0xMTIGRTItMTEzBkUyLTIwMQZFMi0yMDIGRTItMjAzBkUyLTIwNAZFMi0yMDUGRTItMjA2BkUyLTIwNwZFMi0yMDgGRTItMjA5BkUyLTIxMAZFMi0yMTEGRTItMjEyBkUyLTIxMwZFMi0zMDEGRTItMzAyBkUyLTMwMwZFMi0zMDQGRTItMzA1BkUyLTMwNgZFMi0zMDcGRTItMzA4BkUyLTMwOQZFMi0zMTAGRTItMzExBkUyLTMxMgZFMi0zMTMGRTItMzE0BkUyLTMxNQZFMi00MDEGRTItNDAyBkUyLTQwMwZFMi00MDQGRTItNDA1BkUyLTQwNgZFMi00MDcGRTItNDA4BkUyLTQwOQZFMi00MTAGRTItNDExBkUyLTQxMgZFMi00MTMGRTItNDE0BkUyLTQxNQZFMi01MDEGRTItNTAyBkUyLTUwMwZFMi01MDQGRTItNTA1BkUyLTUwNgZFMi01MDcGRTItNTA4BkUyLTUwOQZFMi01MTAGRTItNTExBkUyLTUxMgZFMi01MTMGRTItNTE0BkUyLTUxNQZFMi02MDEGRTItNjAyBkUyLTYwMwZFMi02MDQGRTItNjA1BkUyLTYwNgZFMi02MDcGRTItNjA4BkUyLTYwOQZFMi02MTAGRTItNjExBkUyLTYxMgZFMi02MTMGRTItNjE0BkUyLTYxNQZFMy0xMDEGRTMtMTAyBkUzLTEwMwZFMy0xMDQGRTMtMTA1BkUzLTEwNgZFMy0xMDcGRTMtMjAxBkUzLTIwMgZFMy0yMDMGRTMtMjA0BkUzLTIwNQZFMy0yMDYGRTMtMjA3BkYxLTYxNQZGMS02MTQGRjEtNjEzBkYxLTYxMgZGMS02MTEGRjEtNjEwBkYxLTYwOQZGMS02MDgGRjEtNjA3BkYxLTYwNgZGMS02MDUGRjEtNjA0BkYxLTYwMwZGMS02MDIGRjEtNjAxBkYxLTUxNQZGMS01MTQGRjEtNTEzBkYxLTUxMgZGMS01MTEGRjEtNTEwBkYxLTUwOQZGMS01MDgGRjEtNTA3BkYxLTUwNgZGMS01MDUGRjEtNTA0BkYxLTUwMwZGMS01MDIGRjEtNTAxBkYxLTQxNQZGMS00MTQGRjEtNDEzBkYxLTQxMgZGMS00MTEGRjEtNDEwBkYxLTQwOQZGMS00MDgGRjEtNDA3BkYxLTQwNgZGMS00MDUGRjEtNDA0BkYxLTQwMwZGMS00MDIGRjEtNDAxBkYxLTMxNQZGMS0zMTQGRjEtMzEzBkYxLTMxMgZGMS0zMTEGRjEtMzEwBkYxLTMwOQZGMS0zMDgGRjEtMzA3BkYxLTMwNgZGMS0zMDUGRjEtMzA0BkYxLTMwMwZGMS0zMDIGRjEtMzAxBkYxLTIxNQZGMS0yMTQGRjEtMjEzBkYxLTIxMgZGMS0yMTEGRjEtMjEwBkYxLTIwOQZGMS0yMDgGRjEtMjA3BkYxLTIwNgZGMS0yMDUGRjEtMjA0BkYxLTIwMwZGMS0yMDIGRjEtMjAxBkYxLTExNQZGMS0xMTQGRjEtMTEzBkYxLTExMgZGMS0xMTEGRjEtMTEwBkYxLTEwOQZGMS0xMDgGRjEtMTA3BkYxLTEwNgZGMS0xMDUGRjEtMTA0BkYxLTEwMwZGMS0xMDIGRjEtMTAxBkYyLTYxNQZGMi02MTQGRjItNjEzBkYyLTYxMgZGMi02MTEGRjItNjEwBkYyLTYwOQZGMi02MDgGRjItNjA3BkYyLTYwNgZGMi02MDUGRjItNjA0BkYyLTYwMwZGMi02MDIGRjItNjAxBkYyLTUxNQZGMi01MTQGRjItNTEzBkYyLTUxMgZGMi01MTEGRjItNTEwBkYyLTUwOQZGMi01MDgGRjItNTA3BkYyLTUwNgZGMi01MDUGRjItNTA0BkYyLTUwMwZGMi01MDIGRjItNTAxBkYyLTQxNQZGMi00MTQGRjItNDEzBkYyLTQxMgZGMi00MTEGRjItNDEwBkYyLTQwOQZGMi00MDgGRjItNDA3BkYyLTQwNgZGMi00MDUGRjItNDA0BkYyLTQwMwZGMi00MDIGRjItNDAxBkYyLTMxNQZGMi0zMTQGRjItMzEzBkYyLTMxMgZGMi0zMTEGRjItMzEwBkYyLTMwOQZGMi0zMDgGRjItMzA3BkYyLTMwNgZGMi0zMDUGRjItMzA0BkYyLTMwMwZGMi0zMDIGRjItMzAxBkYyLTIxMgZGMi0yMTEGRjItMjEwBkYyLTIwOQZGMi0yMDgGRjItMjA3BkYyLTIwNgZGMi0yMDUGRjItMjA0BkYyLTIwMwZGMi0yMDIGRjItMjAxBkYyLTExMgZGMi0xMTEGRjItMTEwBkYyLTEwOQZGMi0xMDgGRjItMTA3BkYyLTEwNgZGMi0xMDUGRjItMTA0BkYyLTEwMwZGMi0xMDIGRjItMTAxBkYzLTEwMQZGMy0xMDIGRjMtMTAzBkYzLTEwNAZGMy0xMDUGRjMtMTA2BkYzLTEwNwZGMy0yMDEGRjMtMjAyBkYzLTIwMwZGMy0yMDQGRjMtMjA1BkYzLTIwNgZGMy0yMDcVgAkCMzYCMzcCMzgCMzkCNDACNDECNDICNDMCNDQCNDUCNDYCNDcCNDgCNDkCNTACNTECNTICNTMCNTQCNTUCNTYCNTcCNTgCNTkCNjACNjECNjICNjMCNjQCNjUCNjYCNjcCNjgCNjkCNzACNzECNzICNzMCNzQCNzUCNzYCNzcCNzgCNzkCODACODECODICODMCODQCODUCODYCODcCODgCODkCOTACOTECOTICOTMCOTQCOTUCOTYCOTcCOTgCOTkDMTAwAzEwMQMxMDIDMTAzAzEwNAMxMDUDMTA2AzEwNwMxMDgDMTA5AzExMAMxMTEDMTEyAzExMwMxMTQDMTE1AzExNgMxMTcDMTE4AzExOQMxMjADMTIxAzEyMgMxMjMDMTI0AzEyNQMxMjYDMTI3AzEyOAMxMjkDMTMwAzEzMQMxMzMDMTM0AzEzNQMxMzYDMTM3AzEzOQMxNDADMTQxAzE0MgMxNDMDMTQ0AzE0NQMxNDYDMTQ3AzE0OAMxNDkDMTUwAzE1MQMxNTIDMTUzAzE1NAMxNTUDMTU2AzE1NwMxNTgDMTU5AzE2MQMxNjIDMTYzAzE2NAMxNjUDMTY2AzE2NwMxNjgDMTY5AzE3MAMxNzEDMTcyAzE3MwMxNzUDMTc2AzE3NwMxNzgDMTc5AzE4MAMxODEDMTgyAzE4MwMxODQDMTg1AzE4NgMxODcDMTg4AzE4OQMxOTADMTkxAzE5MgMxOTMDMTk0AzE5NQMxOTYDMTk3AzE5OAMxOTkDMjAwAzIwMQMyMDIDMjAzAzIwNAMyMDUDMjA2AzIwNwMyMDgDMjA5AzIxMAMyMTEDMjEyAzIxMwMyMTQDMjE1AzIxNgMyMTcDMjE4AzIxOQMyMzcDMjM4AzIzOQMyNDADMjQxAzI0MgMyNDMDMjQ0AzI0NQMyNDYDMjQ3AzI0OAMyNDkDMjUwAzI1MQMyNTIDMjU0AzI1NQMyNTYDMjU3AzI1OAMyNTkDMjYwAzI2MQMyNjIDMjYzAzI2NAMyNjUDMjY2AzI2NwMyNjgDMjY5AzI3MAMyNzEDMjcyAzI3MwMyNzQDMjc1AzI3NgMyNzcDMjc4AzI3OQMyODADMjgxAzI4MgMyODMDMjg0AzI4NQMyODYDMjg3AzI4OAMyODkDMjkwAzI5MQMyOTIDMjkzAzI5NAMyOTUDMjk2AzI5NwMyOTgDMjk5AzMwMAMzMDEDMzAyAzMwMwMzMDQDMzA1AzMwNgMzMDcDMzA4AzMwOQMzMTADMzExAzMxMgMzMTMDMzE1AzMxNgMzMTcDMzE4AzMxOQMzMjADMzIxAzMyMgMzMjMDMzI0AzMyNQMzMjYDMzI3AzMyOAMzMjkDMzMwAzMzMQMzMzIDMzMzAzMzNAMzMzUDMzM2AzMzNwMzMzgDMzM5AzM0MAMzNDEDMzQyAzM0MwMzNDQDMzQ3AzM0OAMzNDkDMzUwAzM1MQMzNTIDMzUzAzM1NAMzNTUDMzU2AzM1NwMzNTgDMzU5AzM2MAMzNjEDMzYyAzM2MwMzNjQDMzY1AzM2NgMzNjcDMzY4AzM2OQMzNzADMzcxAzM3MgMzNzMDMzc0AzM3NQMzNzYDMzc3AzM3OAMzNzkDMzgwAzM4MQMzODIDMzgzAzM4NAMzODUDMzg2AzM4NwMzODgDMzg5AzM5MAMzOTEDMzkyAzM5MwMzOTQDMzk1AzM5NgMzOTcDMzk4AzM5OQM0MDADNDAxAzQwMgM0MDMDNDA0AzQwNQM0MDYDNDA3AzQwOAM0MDkDNDEwAzQxMQM0MTIDNDEzAzQxNAM0MTUDNDE2AzQxNwM0MTgDNDE5AzQyMAM0MjEDNDIyAzQyMwM0MjQDNDI1AzQyNgM0MjcDNDI4AzQyOQM0MzADNDMxAzQzMgM0MzMDNDM0AzQzNQM0MzYDNDM3AzQzOAM0MzkDNDQwAzQ0MQM0NDIDNDQzAzQ0NAM0NjQDNDY1AzQ2NgM0NjcDNDY4AzQ2OQM0NzADNDcxAzQ3MgM0NzMDNDc0AzQ3NQM0NzYDNDc3AzQ3OAM0NzkDNDgwAzQ4MQM0ODIDNDgzAzQ4NAM0ODUDNDg2AzQ4NwM0ODgDNDg5AzQ5MAM0OTEDNDkyAzQ5MwM0OTQDNDk1AzQ5NgM0OTcDNDk4AzQ5OQM1MDADNTAxAzUwMgM1MDMDNTA0AzUwNQM1MDYDNTA3AzUwOAM1MDkDNTEwAzUxMQM1MTIDNTEzAzUxNAM1MTUDNTE2AzUxNwM1MTgDNTE5AzUyMAM1MjEDNTIyAzUyMwM1MjQDNTI1AzUyNgM1MjcDNTI4AzUyOQM1MzADNTMxAzUzMgM1MzMDNTM0AzUzNQM1MzYDNTM3AzUzOAM1MzkDNTQwAzU0MQM1NDIDNTQzAzU0NAM1NDUDNTQ2AzU0NwM1NDgDNTQ5AzU1MAM1NTEDNTUyAzU1MwM1NTQDNTU1AzU1NgM1NTcDNTU4AzU2MAM1NjEDNTYyAzU2MwM1NjQDNTY1AzU2NgM1NjcDNTY4AzU2OQM1NzADNTcxAzU3MgM1NzMDNTc0AzU3NQM1NzYDNTc3AzU3OAM1NzkDNTgwAzU4MQM1ODIDNTgzAzU4NAM1ODUDNTg2AzU4NwM1ODgDNTg5AzU5MAM1OTEDNTkyAzU5MwM1OTQDNTk1AzU5NgM1OTcDNTk4AzU5OQM2MDADNjAxAzYwMgM2MDMDNjA0AzYwNQM2MDYDNjA3AzYwOAM2MDkDNjEwAzYxMQM2MTIDNjEzAzYxNAM2MTUDNjE2AzYxNwM2MTgDNjE5AzYyMAM2MjEDNjIyAzYyMwM2MjQDNjI1AzYyNgM2MjcDNjI4AzYyOQM2MzADNjMxAzYzMgM2MzMDNjM0AzYzNQM2MzYDNjM3AzYzOAM2MzkDNjQwAzY0MQM2NDIDNjQzAzY0NAM2NDUDNjQ2AzY0NwM2NDgDNjQ5AzY1MAM2NTEDNjUyAzY1MwM2NTQDNjU1AzY1NgM2NTcDNjU4AzY1OQM2NjADNjYxAzY2MgM2NjMDNjY0AzY2NQM2NjYDNjY3AzY2OAM2NjkDNjcwAzY3MQM2NzIDNjczAzY3NAM2NzUDNjc2AzY3NwM2NzgDNjc5AzY4MAM2ODEDNjgyAzY4MwM2ODQDNjg1AzY4NgM2ODcDNjg4AzY4OQM2OTADNjkxAzY5MgM2OTMDNjk0AzY5NQM2OTYDNjk3AzY5OAM2OTkDNzAwAzcwMQM3MDIDNzAzAzcwNAM3MDUDNzA2AzcwNwM3MDgDNzA5AzcxMAM3MTEDNzEyAzcxMwM3MTQDNzE1AzcxNgM3MTcDNzE4AzcxOQM3MjADNzIxAzcyMgM3MjMDNzI0AzcyNQM3MjYDNzI3AzcyOAM3MjkDNzMwAzczMQM3MzIDNzMzAzczNAM3MzUDNzM2AzczNwM3MzgDNzM5Azc0MAM3NDEDNzQyAzc0MwM3NDQDNzQ1Azc0NgM3NDcDNzQ4Azc0OQM3NTADNzUxAzc1MgM3NTMDNzU0Azc1NQM3NTYDNzU3Azc1OAM3NTkDNzYwAzc2MQM3NjIDNzYzAzc2NAM3NjUDNzY2Azc2NwM3NjgDNzY5Azc3MAM3NzEDNzcyAzc3MwM3NzQDNzc1Azc3NgM3NzcDNzc4Azc3OQM3ODADNzgxAzc4MgM3ODMDNzg0Azc4NQM3ODYDNzg3Azc4OAM3ODkDNzkwAzc5MQM3OTIDNzkzAzc5NAM3OTUDNzk2Azc5NwM3OTgDNzk5AzgwMAM4MDEDODAyAzgwMwM4MDQDODA1AzgwNgM4MDcDODA4AzgwOQM4MTADODExAzgxMgM4MTMDODE0AzgxNQM4MTYDODE3AzgxOAM4MTkDODIwAzgyMQM4MjIDODIzAzgyNAM4MjUDODI2AzgyNwM4MjgDODI5AzgzMAM4MzEDODMyAzgzMwM4MzQDODM1AzgzNgM4MzcDODM4AzgzOQM4NDADODQxAzg0MgM4NDMDODQ0Azg0NQM4NDYDODQ3Azg0OAM4NjMDODY0Azg2NQM4NjYDODY3Azg2OAM4NjkDODcwAzg3MQM4NzIDODczAzg3NAM4NzUDODc2Azg3NwM4NzgDODc5Azg4MAM4ODEDODgyAzg4MwM4ODQDODg1Azg4NgM4ODcDODg4Azg4OQM4OTADODkxAzg5MgM4OTMDODk0Azg5NQM4OTYDODk3Azg5OAM4OTkDOTAwAzkwMQM5MDIDOTAzAzkwNAM5MDUDOTA2AzkwNwM5MDkDOTEwAzkxMQM5MTIDOTEzAzkxNAM5MTUDOTE2AzkxNwM5MTgDOTE5AzkyMAM5MjEDOTIyAzkyMwM5MjQDOTI1AzkyNgM5MjcDOTI4AzkyOQM5MzADOTMxAzkzMgM5MzMDOTM0AzkzNQM5MzYDOTM3AzkzOAM5MzkDOTQwAzk0MQM5NDIDOTQzAzk0NAM5NDUDOTQ2Azk0NwM5NDgDOTQ5Azk1MAM5NTEDOTUyAzk1MwM5NTQDOTU1Azk1NgM5NTcDOTU4Azk1OQM5NjADOTYxAzk2MgM5NjMDOTY0Azk2NQM5NjYDOTY3Azk2OAM5NjkDOTcwAzk3MQM5NzIDOTc1Azk3NgM5NzcDOTc4Azk3OQM5ODADOTgxAzk4MgM5ODMDOTg0Azk4NQM5ODYDOTg3Azk5MAM5OTEDOTkyAzk5MwM5OTQDOTk1Azk5NgM5OTcDOTk4Azk5OQQxMDAwBDEwMDEEMTAwMgQxMDAzBDEwMDQEMTAwNQQxMDA2BDEwMDcEMTAwOAQxMDA5BDEwMTAEMTAxMQQxMDEyBDEwMTMEMTAxNAQxMDE1BDEwMTYEMTAxNwQxMDE4BDEwMTkEMTAyMAQxMDIxBDEwMjIEMTAyMwQxMDI0BDEwMjUEMTAyNgQxMDI3BDEwMjgEMTAyOQQxMDMwBDEwMzEEMTAzMgQxMDMzBDEwMzQEMTAzNQQxMDM2BDEwMzcEMTAzOAQxMDM5BDEwNDAEMTA0MQQxMDQyBDEwNDMEMTA0NAQxMDQ1BDEwNDYEMTA0NwQxMDQ4BDEwNDkEMTA1MQQxMDUyBDEwNTMEMTA1NAQxMDU1BDEwNTYEMTA1NwQxMDU4BDEwNTkEMTA2MAQxMDYxBDEwNjIEMTA2MwQxMDY0BDEwNjUEMTA2NgQxMDY3BDEwNjgEMTA2OQQxMDcwBDEwNzEEMTA3MgQxMDczBDEwNzQEMTA3NQQxMDc2BDEwNzcEMTA3OAQxMDc5BDEwODAEMTA4MQQxMDgyBDEwODMEMTA4NAQxMDg1BDEwODYEMTA4NwQxMDg4BDEwODkEMTA5MAQxMDkxBDEwOTIEMTA5MwQxMDk0BDEwOTUEMTA5NgQxMDk3BDEwOTgEMTA5OQQxMTAwBDExMDEEMTEwMgQxMTAzBDExMDQEMTEwNQQxMTA2BDExMDcEMTEwOAQxMTA5BDExMTAEMTExMQQxMTEyBDExMTMEMTExNAQxMTE1BDExMTYEMTExNwQxMTE4BDExMTkEMTEyMAQxMTIxBDExMjIEMTEyMwQxMTI0BDExMjUEMTEyNgQxMTI3BDExMjgEMTEyOQQxMTMwBDExMzEEMTEzMgQxMTMzBDExMzQEMTEzNQQxMTM2BDExMzcEMTEzOAQxMTM5BDExNDAEMTE0MQQxMTQyBDExNDMEMTE0NAQxMTQ1BDExNDYEMTE0NwQxMTQ4BDExNDkEMTE1MAQxMTUxBDExNTIEMTE1MwQxMTU0BDExNTUEMTE1NgQxMTU3BDExNTgEMTE1OQQxMTYwBDExNjEEMTE2MgQxMTYzBDExNjQEMTE2NQQxMTY2BDExNjcEMTE2OAQxMTY5BDExNzAEMTE3MQQxMTcyBDExNzMEMTE3NAQxMTc1BDExNzYEMTE3NwQxMTc4BDExNzkEMTE4MAQxMTgxBDExODIEMTE4MwQxMTg0BDExODUEMTE4NgQxMTg3BDExODgEMTE4OQQxMTkwBDExOTEEMTE5MgQxMTkzBDExOTQEMTE5NQQxMTk2BDExOTcEMTE5OAQxMTk5BDEyMDAEMTIwMQQxMjAyBDEyMDMEMTIwNAQxMjA1BDEyMDYEMTIwNwQxMjA4BDEyMDkEMTIxMAQxMjExBDEyMTIEMTIxMwQxMjE0BDEyMTUEMTIxNgQxMjE3BDEyMTgEMTIxOQQxMjIwBDEyMjEEMTIyMgQxMjIzBDEyMjQEMTIyNQQxMjI2BDEyMjcEMTIyOAQxMjI5BDEyMzAEMTIzMQQxMjMyBDEyMzMEMTIzNAQxMjM1BDEyMzYEMTIzNwQxMjM4BDEyMzkEMTI0MAQxMjQxBDEyNDIEMTI0MwQxMjQ0BDEyNDUEMTI0NgQxMjQ3BDEyNDgEMTI0OQQxMjUwBDEyNTEEMTI1MhQrA4AJZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZGQYAQUeX19Db250cm9sc1JlcXVpcmVQb3N0QmFja0tleV9fFgEFBWJ0bk9LVZOxLBxq3klNHRDDmNX5vJz+du/t7mxCWmzEcPMt0So='
        __eventvalidation = r'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'

        data = {
            'lsArea': room_object.building.encode('gbk'),
            'lsRoom': room_object.value.encode('gbk'),
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__LASTFOCUS': '',
            '__VIEWSTATE': __viewstate,
            '__EVENTVALIDATION': __eventvalidation,
            '__smartNavPostBack': 'true',
            'btnOK.x': random.randint(0, 100),
            'btnOK.y': random.randint(0, 100),
        }
        res = self.session.post(URL_ELECTRICITY_GET_BUILDINGS, data=data,
                                headers=gen_header_referer_electricity())
        content = res.content.decode('gbk')
        return content.find('/Cardholder/SelfHelpPay.aspx') != -1
