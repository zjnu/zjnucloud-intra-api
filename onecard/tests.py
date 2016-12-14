from lxml import etree
import random
from django.test import TestCase

# Create your tests here.
from onecard import core

import requests
from onecard.models import OneCardElectricityBuilding, OneCardElectricityRoom


class OneCardTestCase(TestCase):

    def setUp(self):
        self.session = core.Session('201532800126', '218023')
        self.session.login()

    # def test_daily_transaction(self):
    #     pass
    #     # print(self.transaction.get_daily())
    #
    # def test_monthly_transaction(self):
    #     print(self.transaction.get_monthly(2016, 6))

    def test_elec_buildings(self):
        building_objects = OneCardElectricityBuilding.objects.all()
        current_building = None
        for room in OneCardElectricityRoom.objects.all():
            related_building = building_objects.get(name=room.building)
            if current_building is None or related_building.name != current_building.name:
                current_building = related_building
            data = {
                'lsArea': room.building.encode('gbk'),
                'lsRoom': room.value,
                '__VIEWSTATE': related_building.viewstate,
                '__EVENTVALIDATION': related_building.eventvalidation,
                '__EVENTTARGET': '',
                '__smartNavPostBack': 'true',
                '__EVENTARGUMENT': '',
                '__LASTFOCUS': '',
                'btnOK.x': random.randint(0, 100),
                'btnOK.y': random.randint(0, 100),
            }
            res = self.session.post('http://ykt.zjnu.edu.cn/Cardholder/SelfHelpElec.aspx',
                                    headers=core.gen_header_referer_electricity(),
                                    data=data)
            content = res.content.decode('gbk')
            selector = etree.HTML(content)
            balance = selector.xpath(r'//select[@id="lblItem"]/text()')
            if balance:
                print(balance)
