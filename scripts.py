import re
import random

from lxml import etree
import requests

from onecard import core
from onecard.models import OneCardElectricityRoom, OneCardElectricityBuilding

URL_LOGIN = 'http://ykt.zjnu.edu.cn/'
URL_MAIN = 'http://ykt.zjnu.edu.cn/Cardholder/Cardholder.aspx'
URL_ELECTRICITY_GET_BUILDINGS = 'http://ykt.zjnu.edu.cn/Cardholder/SelfHelpElec.aspx'


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


def gen_header_referer_electricity():
    header = gen_header_base()
    header.update({
        'Accept': 'image/gif, image/jpeg, image/pjpeg, application/x-ms-application, '
                  'application/xaml+xml, application/x-ms-xbap, */*',
        'Referer': URL_ELECTRICITY_GET_BUILDINGS,
        'Pragma': 'no-cache',
    })
    return header


def parse_onecard_captcha(content):
        selector = etree.HTML(content)
        arrs = selector.xpath(r'//*[@bgcolor="#d6cece"]//img')
        captcha = str()
        for each in arrs:
            captcha += re.search(r'(\d)', each.attrib['src'], re.S).group(0)
        return captcha


def get_electricity_room_extras():
    s = requests.session()
    # 1. Login
    html = s.get(URL_LOGIN, headers=gen_header_base())
    html.encoding = 'gbk'
    content = html.content.decode('gbk')
    __viewstate, __eventvalidation = core.Session.parse_body_extras(content)
    captcha = parse_onecard_captcha(content)
    data = {
        '__VIEWSTATE': __viewstate,
        '__EVENTVALIDATION': __eventvalidation,
        'UserLogin:txtUser': '201532800126',
        'UserLogin:txtPwd': '218023',
        'UserLogin:ddlPerson': '卡户'.encode('gbk'),
        'UserLogin:txtSure': captcha,
        'UserLogin:ImageButton1.x': random.randint(0, 100),
        'UserLogin:ImageButton1.y': random.randint(0, 100),
    }
    s.post(URL_LOGIN, data=data, headers=gen_header_referer_is_logged_in())

    # 2. Get each building extras
    res = s.get(URL_ELECTRICITY_GET_BUILDINGS, headers=gen_header_base())
    content = res.content.decode('gbk')
    __viewstate, __eventvalidation = core.Session.parse_body_extras(content)
    selector = etree.HTML(content)
    building_names = selector.xpath(r'//select[@name="lsArea"]/option/text()')
    building_objects = [OneCardElectricityBuilding(name=building_name) for building_name in building_names]
    OneCardElectricityBuilding.objects.bulk_create(building_objects)
    for building in OneCardElectricityBuilding.objects.all():
        data = {
            'lsArea': building.name.encode('gbk'),
            '__VIEWSTATE': __viewstate,
            '__EVENTVALIDATION': __eventvalidation,
            '__EVENTTARGET': 'lsArea',
            '__smartNavPostBack': 'true',
            '__EVENTARGUMENT': '',
            '__LASTFOCUS': '',
        }
        res = s.post(URL_ELECTRICITY_GET_BUILDINGS,
                     headers=gen_header_referer_electricity(),
                     data=data)
        content = res.content.decode('gbk')
        building.viewstate, building.eventvalidation = core.Session.parse_body_extras(content)
        building.save()

    # for index, building in enumerate(buildings):
    #     selector = etree.HTML(content)
    #     rooms = selector.xpath(r'//select[@name="lsRoom"]/option')
    #     for room in rooms:
    #         value = room.attrib['value']
    #         room_no = room.text
    #         data = {
    #             'lsArea': building.encode('gbk'),
    #             'lsRoom': room_no,
    #             '__VIEWSTATE': __viewstate,
    #             '__EVENTVALIDATION': __eventvalidation,
    #             '__EVENTTARGET': '',
    #             '__smartNavPostBack': 'true',
    #             '__EVENTARGUMENT': '',
    #             '__LASTFOCUS': '',
    #             'btnOK.x': random.randint(0, 100),
    #             'btnOK.y': random.randint(0, 100),
    #         }
    #         res = s.post(URL_ELECTRICITY_GET_BUILDINGS,
    #                      headers=gen_header_referer_electricity(),
    #                      data=data)
    #         content = res.content.decode('gbk')
    #         selector = etree.HTML(content)
    #         target_viewstate = selector.xpath
    #         room_object = OneCardElectricityRoom.objects.get(room=room_no, value=value)


if __name__ == '__main__':
    get_electricity_room_extras()
