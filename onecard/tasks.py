from lxml import etree
import re
import time

from celery.app import shared_task

from common.push import BmobPushMessage
from onecard.models import OneCardCharge

URL_ONLINE_BANK_CHARGE = 'http://ykt.zjnu.edu.cn/Cardholder/Onlinebank.aspx'
MSG_ONLINE_BANK_CHARGE_SUCCESS = '一卡通充值已成功！充值金额为{}元'
RESULT_CODE_ONLINE_BANK_CHARGE_UNKNOWN = -1
RESULT_CODE_ONLINE_BANK_CHARGE_TRANSFER_SUCCESS = 1
RESULT_CODE_ONLINE_BANK_CHARGE_BANK_BALANCE_INSUFFICIENT = 2


def gen_header_referer_online_bank():
    return {
        'Accept': 'text/html, application/xhtml+xml, image/jxr, */*',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-Hans-CN,zh-Hans;q=0.8,en-US;q=0.5,en;q=0.3',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
        'Referer': URL_ONLINE_BANK_CHARGE,
        'Pragma': 'no-cache',
    }


@shared_task
def refresh_charge_status(session, username, amount, post_data, charge_object_id, push_credential):
    print(push_credential)
    message = ''

    while message != '您的转账申请还在处理中，请稍后！':
        print('Wait 30 secs...')
        time.sleep(30)
        res = session.post(URL_ONLINE_BANK_CHARGE, data=post_data, headers=gen_header_referer_online_bank())
        result_content = res.content.decode('gbk')
        if result_content.find("您的转账申请还在处理中，请稍后！") == -1:
            message = re.findall(r"alert\('(.*?)'", result_content, re.S)
            if message:
                message = message[0]
                # Update charge object
                charge_object = OneCardCharge.objects.get(pk=charge_object_id)
                if message.find('恭喜你，转账成功') != -1:
                    message = MSG_ONLINE_BANK_CHARGE_SUCCESS.format(amount)
                    charge_object.result = RESULT_CODE_ONLINE_BANK_CHARGE_TRANSFER_SUCCESS
                elif message.find('转账失败，请检查银行卡余额是否不足') != -1:
                    charge_object.result = RESULT_CODE_ONLINE_BANK_CHARGE_BANK_BALANCE_INSUFFICIENT
                else:
                    charge_object.result = RESULT_CODE_ONLINE_BANK_CHARGE_UNKNOWN
                charge_object.message = message
                charge_object.save()

                push_message(message, push_credential)
                # Log out
                session.close()
                return 'User ' + username + ': ' + message
            break


def push_message(message, push_credential):
    if message and push_credential:
        device_type, credential = push_credential.split(' ')
        BmobPushMessage().send_single(device_type, credential, message)


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
