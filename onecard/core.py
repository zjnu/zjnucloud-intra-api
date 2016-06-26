from collections import OrderedDict
import random
import re
import base64
import decimal

from lxml import etree
import requests

from onecard.models import OneCardUser, OneCardElectricityBuildings


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
STATUS_ONLINE_BANK_CHARGE_SUCCESS = 101100
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
MSG_ONLINE_BANK_CHARGE_SUCCESS = '转账申请成功，到账可能会有延迟，请耐心等待！'
MSG_ONLINE_BANK_CHARGE_ERR_UNKNOWN = '未知错误'
MSG_ONLINE_BANK_CHARGE_INVALID_AMOUNT = '非法的充值金额，请重新输入！'
MSG_ONLINE_BANK_CHARGE_INVALID_AMOUNT_ZERO = '充值金额必须大于0！'
MSG_ONLINE_BANK_CHARGE_PAY_PASSWORD_WRONG = '交易密码错误，请重新输入！'
MSG_ONLINE_BANK_CHARGE_AMOUNT_LIMIT = '由于安全原因，充值金额不得超过1000元！'
MSG_ELECTRICITY_BUILDINGS_CREATED = '所有楼房已获取'
MSG_ELECTRICITY_BUILDINGS_NOT_FOUND = '未找到对应房间号'
MSG_ELECTRICITY_GET_ROOM_INFO_FAILED = '未能获取房间电量信息'

# Results
# Stands for charge in process
RESULT_CODE_ONLINE_BANK_CHARGE_TRANSFER_IN_PROCESS = 0
# Stands for charge complete successfully
RESULT_CODE_ONLINE_BANK_CHARGE_TRANSFER_SUCCESS = 1

# Limits
ONECARD_USER_LIMIT = 1
ONECARD_CHARGE_AMOUNT_LIMIT = 1000


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

    def charge(self, amount, pay_password):
        if self.code == STATUS_SUCCESS:
            # Must get __VIEWSTATE and __EVENTVALIDATION first
            html = self.session.get(URL_ONLINE_BANK_CHARGE, headers=gen_header_referer_is_logged_in(True))
            __viewstate, __eventvalidation = Session.parse_body_extras(html.content.decode('gbk'))
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
                # TODO: Send push message
                # Log out
                self.session.logout()
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
            self.response_data['code'] = STATUS_ONLINE_BANK_CHARGE_SUCCESS
            self.response_data['message'] = MSG_ONLINE_BANK_CHARGE_SUCCESS
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
        is_empty_table = True if not OneCardElectricityBuildings.objects.all() else False
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
                    room_objects.append(OneCardElectricityBuildings(building=building, room=text, value=value))
                else:
                    OneCardElectricityBuildings.objects.get_or_create(building=building, room=text, value=value)

        # Do bulk_create
        if is_empty_table:
            OneCardElectricityBuildings.objects.bulk_create(room_objects)

        self.response_data['message'] = MSG_ELECTRICITY_BUILDINGS_CREATED
        self.response_data['result'] = None
        return self.response_data

    def get_room_info(self, building, room):
        try:
            _room = OneCardElectricityBuildings.objects.filter(building=building, room=room)[0]
            if not self.__post_room_data(_room):
                self.response_data['code'] = STATUS_SUCCESS
                self.response_data['message'] = MSG_ELECTRICITY_GET_ROOM_INFO_FAILED
                return self.response_data

            res = self.session.get(URL_ELECTRICITY_PAY, headers=gen_header_referer_electricity())
            content = res.content.decode('gbk')
            self.parse_room_info(content)

        except OneCardElectricityBuildings.DoesNotExist:
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
        html = self.session.get(URL_ELECTRICITY_GET_BUILDINGS, headers=gen_header_referer_electricity())
        __viewstate, __eventvalidation = Session.parse_body_extras(html.content.decode('gbk'))

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
