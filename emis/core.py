from collections import OrderedDict
from io import BytesIO

from django.utils.datastructures import MultiValueDictKeyError
import requests
import re
from PIL import Image
from lxml import etree
import time
import random

from emis import ocr
from emis.exceptions import CaptchaIsNotNumberException

__author__ = 'ddmax'

# EMIS_URL
URL_LOGIN = 'http://10.1.68.13:8001/login.asp'
URL_LOGOUT = 'http://10.1.68.13:8001/loginOut.asp'
URL_CODE = 'http://10.1.74.13/checkcode.asp'
URL_TERMSCORE = 'http://10.1.68.13:8001/studentWeb/ViewScore/ViewTermScore.asp'
URL_TOTALSCORE = 'http://10.1.68.13:8001/studentWeb/ViewScore/ViewTotalScore.asp'
URL_COURSETABLE = 'http://10.1.68.13:8001/studentWeb/SelectCourse/displayhistory.asp'
URL_EXAMSCHEDULE = 'http://10.1.68.13:8001/studentWeb/Examination/ViewExam1.asp'

# Session status code
STATUS_ERR_PARAM = -2
STATUS_ERR_UNKNOWN = -1
STATUS_SUCCESS = 0  # Login success
STATUS_ERR_USERNAME = 1  # Username invalid
STATUS_ERR_PASSWORD = 2  # Password invalid
STATUS_ERR_CODE = 4  # Captcha invalid & other // TODO
STATUS_ERR_EMIS = 4  # EMIS error
STATUS_EXCEED_BMOB_BIND_TIMES_LIMIT = 10  # Exceed bmob account bind times limit
STATUS_EXCEED_EMIS_BIND_TIMES_LIMIT = 11  # Exceed EMIS account bind times limit

# Messages
MSG_ERR_PARAM = '参数错误'
MSG_ERR_UNKNOWN = '未知错误'
MSG_SUCCESS = ''  # Login success
MSG_ERR_USERNAME = '账号不存在哦，请检查账号是否输入正确。'  # Username invalid
MSG_ERR_PASSWORD = '你的密码输错了呢，请检查。'  # Password invalid
MSG_ERR_CODE = '教务系统已关闭，本学期将不再会有数据更新，请在下学期开学前后再访问'  # Captcha invalid
# MSG_ERR_CODE = '我们的服务器出现了异常，程序猿正在玩命抢修中。。。'  # Captcha invalid
MSG_ERR_EMIS = '教务系统的访问量太高，过会儿再访问吧！'  # EMIS error
MSG_BMOB_BIND_TIMES_COUNT = '绑定成功！你还能绑定{}个教务账号。'  # Exceed bmob account bind times limit
# MSG_EMIS_BIND_TIMES_COUNT = ''  # Exceed EMIS account bind times limit
MSG_EXCEED_BMOB_BIND_TIMES_LIMIT = '你绑定过的教务账号太多了呢，请联系我们处理。'  # Exceed bmob account bind times limit
MSG_EXCEED_EMIS_BIND_TIMES_LIMIT = '该教务账号已被{}个人绑定，太丧病了吧！请联系我们处理。'  # Exceed EMIS account bind times limit


def init(username, password, usertype='student'):
    session = Session(username, password, usertype)
    status, message = session.login()
    return session, status, message


# Headers
def gen_random_header():
    return {
        # 'User-Agent': 'Googlebot/2.1 (+http://www.google.com/bot.html)',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:43.0) Gecko/20100101 Firefox/43.0',
        'X-Real-IP': '10.11.12.' + str(random.randint(1, 253)),
        'X-Forwarded-For': '222.223.233.' + str(random.randint(1, 253)),
    }


def fuckthedog(seconds=0.2):
    # Avoid the fucking safedog
    time.sleep(seconds)
    print('Slept ' + str(seconds) + 's, continue')


class Session(requests.Session):

    def __init__(self, username='', password='', usertype='student'):
        super().__init__()
        self.username = username
        self.password = password
        self.usertype = usertype
        # Result code represents session status
        self.result_code = 0

    def login(self):
        global result, request_times
        print('Start login...')
        # Try to do 10 times to do captcha
        request_times = 0
        while self.result_code != 200 and request_times < 10:
            request_times += 1
            # print('Attempt to get checkcode...')
            # Fetch captcha

            fuckthedog()
            codeimg = self.get(URL_CODE, headers=gen_random_header())
            print('Checkcode captured: ', end='')
            imgbytes = codeimg.content
            # Recognize the captcha
            # with open('code.bmp', 'wb') as f:
            #     f.write(imgbytes)
            # code = input('Please input code:')
            try:
                image = Image.open(BytesIO(imgbytes))
                code = ocr.ocr_captcha(image)
                print(code)
            except IOError as e:
                # print(e)
                continue
            except CaptchaIsNotNumberException as ce:
                print(ce)
                fuckthedog()
                continue

            # Post data
            data = {
                'radioUserType': self.usertype,
                'userId': self.username,
                'pwd': self.password,
                'GetCode': code,
            }

            # Perform login
            fuckthedog()
            result = self.post(URL_LOGIN, data=data, headers=gen_random_header())
            # with open('result.html', 'wb') as f:
            #     f.write(result.content.decode('gbk').encode('utf-8'))
            self.result_code = result.status_code

        status, message = self.check_status(result.content.decode('gbk'))
        return status, message

    def check_status(self, content):
        if self.result_code == 200:
            if content.find('当前用户账号不存在') != -1:
                return STATUS_ERR_USERNAME, MSG_ERR_USERNAME
            elif content.find('当前用户密码错误') != -1:
                return STATUS_ERR_PASSWORD, MSG_ERR_PASSWORD
            elif content.find('验证码输入错误') != -1 or \
                 content.find('浙江师范大学教务管理系统EMIS') == -1:
                # Captcha error or other situations that indicate login error
                return STATUS_ERR_CODE, MSG_ERR_CODE
            else:
                # Login success!
                return STATUS_SUCCESS, MSG_SUCCESS
        print('EMIS banned!')
        return STATUS_ERR_EMIS, MSG_ERR_EMIS

    def logout(self,):
        print('Success, logged out!')
        fuckthedog()
        self.get(URL_LOGOUT, headers=gen_random_header())
        self.close()


class EmisBase:

    def __init__(self, request):
        self.response_data = OrderedDict()
        try:
            if request is not None:
                # Detect request method
                if request.method == 'POST':
                    self.username = request.data['username']
                    self.password = request.data['password']
                # Log in
                self.session, self.status, self.message = init(self.username, self.password)
        except MultiValueDictKeyError:
            self.status = STATUS_ERR_PARAM
            self.message = MSG_ERR_PARAM
        # Append status and message
        self.response_data['status'] = self.status
        self.response_data['message'] = self.message


class Score(EmisBase):

    def __init__(self, request):
        super().__init__(request)

    def get_total_score(self):
        # If login success, get scores
        if self.status == STATUS_SUCCESS:
            print('Getting total score...')
            fuckthedog(1)
            total_score = self.session.post(URL_TOTALSCORE, headers=gen_random_header())
            total_score.encoding = 'gbk'
            content = total_score.content.decode('gbk')
            # with open('termscore.html', 'wb') as f:
            #     f.write(content)
            # Parse the data with xpath
            self.parse(content)
            # Log out
            self.session.logout()
        else:
            # Empty score if login failed
            self.response_data['scores'] = list()
        return self.response_data

    def parse(self, content):
        """
        Parse the html based content to OrderedDict in order to
        be serialized to JSON
        """
        selector = etree.HTML(content)
        # Student name
        banner_content = str(selector.xpath(r'//div/p/b/font/span/text()')[0]).strip()
        self.response_data['name'] = banner_content[0:banner_content.index('同学')]
        # Total credits
        total_credits = str(selector.xpath(r'//div/p/font/text()')[0]).strip()
        self.response_data['credits'] = total_credits
        # GPA
        gpa = str(selector.xpath(r'//div/p/font/text()')[1]).strip()
        self.response_data['gpa'] = gpa
        # Score table
        all_data_cells = selector.xpath(r'//table/tr[position()>1]')
        all_data_cells.reverse()
        # Semester info
        semesters = list()
        for each in all_data_cells:
            value = str(each.xpath(r'./td/div/text()')[0]).strip()
            if value not in semesters:
                semesters.append(value)
        # Divide scores with each semester
        scores = list()
        for name in semesters:
            each_semester = dict()
            each_semester['semester'] = name[:-1] + '学年第' + name[-1:] + '学期'
            self.parse_semester_gpa(name[:-1], name[-1:], each_semester)
            values = list()
            for each in all_data_cells:
                if str(each.xpath(r'./td/div/text()')[0]).strip() == name:
                    info = OrderedDict()
                    info['id'] = str(each.xpath(r'./td/div/text()')[1]).strip()
                    info['name'] = str(each.xpath(r'./td/div/text()')[2]).strip()
                    info['credit'] = str(each.xpath(r'./td/div/text()')[3]).strip()
                    info['mark'] = str(each.xpath(r'./td/div/text()')[4]).strip()
                    info['makeupmark'] = str(each.xpath(r'./td/div/text()')[5]).strip()
                    info['retakemark'] = str(each.xpath(r'./td/div/text()')[6]).strip()
                    info['gradepoint'] = str(each.xpath(r'./td/div/text()')[7]).strip()
                    values.append(info)
            each_semester['values'] = values
            scores.append(each_semester)
        self.response_data['count'] = len(all_data_cells)
        self.response_data['scores'] = scores

    def parse_semester_gpa(self, year, semester, result_dict):
        """
        Get and parse credits and gpa of each semester
        :param year: a number, ex. 2014
        :param semester: a number, 1 or 2
        :param result_dict: target dict of each semester
        """
        # Post data
        data = {
            'textYear': year,
            'SelectTerm': semester,
        }
        semester_score = self.session.post(URL_TERMSCORE, data=data)
        semester_score.encoding = 'gbk'
        content = semester_score.content.decode('gbk')
        selector = etree.HTML(content)
        # Semester's credits and gpa
        result_dict['credits'] = str(selector.xpath(r'//div/p/font/text()')[0]).strip()
        result_dict['gpa'] = str(selector.xpath(r'//div/p/font/text()')[1]).strip()


class CourseTable(EmisBase):

    def __init__(self, request):
        super().__init__(request)

    def get_course_table(self, year, semester):
        # If login success, get scores
        if self.status == STATUS_SUCCESS:
            print('Getting course table...')
            fuckthedog()
            params = '?year=' + year \
                     + '&nouse=' + str(int(year) + 1) \
                     + '&select=' + semester
            courses = self.session.get(URL_COURSETABLE + params, headers=gen_random_header())
            courses.encoding = 'gbk'
            content = courses.content.decode('gbk')
            # Parse the data with xpath
            self.parse(content)
            # Log out
            self.session.logout()
        else:
            # Empty score if login failed
            self.response_data['courses'] = list()
        return self.response_data

    def parse(self, content):
        # f = open('testdata.html', encoding='utf8')
        # selector = etree.HTML(f.read())
        selector = etree.HTML(content)
        # Banner which contains name and info
        banner_content = selector.xpath(r'//p')[0]
        self.response_data['name'] = str(banner_content.xpath(r'./font/b/text()')[0]).strip()
        self.response_data['info'] = str(banner_content.xpath(r'./font/b/font/text()')[0]).strip()
        # All courses in current semester
        all_courses_data = selector.xpath(r'//table/tr[position()>1]')
        courses = list()
        for each in all_courses_data:
            info = OrderedDict()
            field_cleaned = self.clean_field(each.xpath(r'./td'))
            info['no'] = self.populate_field(field_cleaned, 0)
            info['id'] = self.populate_field(field_cleaned, 1)
            info['name'] = self.populate_field(field_cleaned, 2)
            info['teacher'] = self.populate_field(field_cleaned, 3)
            info['time'] = self.populate_field(field_cleaned, 4)
            info['classroom'] = self.populate_field(field_cleaned, 5)
            info['total'] = self.populate_field(field_cleaned, 6)
            info['elected'] = self.populate_field(field_cleaned, 7)
            info['credit'] = self.populate_field(field_cleaned, 8)
            info['property'] = self.populate_field(field_cleaned, 9)
            info['remarks'] = self.populate_field(field_cleaned, 10)
            courses.append(info)
        self.response_data['courses'] = courses

    def clean_field(self, fields):
        field_cleaned = list()
        for i, field in enumerate(fields):
            # Check whether current node has some child nodes
            # If yes, generate the children_text
            children = field.xpath(r'./*')
            children_text = self.clean_children(children, str())
            # Concat text in current node and its children
            val = self.concat_field(str(field.text).strip(), children_text)
            # Deal with time (which located at 5th <td>), split it to list
            if i == 4:
                vals = self.deal_time(val)
                field_cleaned.append(vals)
            else:

                field_cleaned.append(val)
        return field_cleaned

    def clean_children(self, children, children_text):
        if len(children) == 0:
            return children_text
        if len(children) > 0:
            for child in children:
                if child.tail is not None:
                    c_tail = str(child.tail).strip()
                    if c_tail != '':
                        if children_text == '':
                            children_text += str(child.tail).strip()
                        else:
                            children_text += ', ' + str(child.tail).strip()
                if child.text is not None:
                    c_text = str(child.text).strip()
                    if c_text != '':
                        if children_text == '':
                            children_text += str(child.text).strip()
                        else:
                            children_text += ', ' + str(child.text).strip()
                return self.clean_children(child.xpath(r'./*'), children_text)

    def concat_field(self, val, child):
        if child != '':
            if val != '':
                val += ', ' + child
            else:
                val += child
        return val

    def populate_field(self, fields, suffix):
        try:
            return fields[suffix]
        except IndexError:
            return ''

    def deal_time(self, time):
        group = re.findall(r'((?:一|二|三|四|五|六|七|日)(?:\d+,)+)', time, re.S)
        # Fix issue one single day contains multiple course time, eg. "三1,2,8,9,"
        for each in group:
            day = each[:1]
            times = each[1:].split(',')
            val = str()
            is_inconsecutive = False
            for i, v1 in enumerate(times):
                # Check whether the time is consecutive
                val = val + v1 + ',' if v1 != '' else val
                try:
                    v1 = int(v1) + 1
                    v2 = int(times[i+1])
                    if v1 != v2:
                        # If not consecutive, append separate time to group
                        is_inconsecutive = True
                        group.append(day + val)
                        val = ''
                except ValueError:
                    continue
            if is_inconsecutive:
                # If inconsecutive, remove the original time
                group.remove(each)
                # append the last time
                group.append(day + val)
        return group

    def deal_classroom(self, classroom):
        res_str = classroom.xpath('string(.)')
        group = re.findall(r'(\d+-\d+|\S+)', res_str, re.S)
        final_str = ''
        for i in range(0, len(group) - 1):
            final_str += group[i] + ', '
        final_str += group[len(group) - 1]
        return final_str


class Exam(EmisBase):

    def __init__(self, request):
        super().__init__(request)

    def get_exam_schedule(self):
        # If login success, get scores
        if self.status == STATUS_SUCCESS:
            print('Getting exam ...')
            fuckthedog()
            exams = self.session.get(URL_EXAMSCHEDULE, headers=gen_random_header())
            exams.encoding = 'gbk'
            content = exams.content.decode('gbk')
            # Parse the data with xpath
            self.parse(content)
            # Log out
            self.session.logout()
        else:
            # Empty score if login failed
            self.response_data['exams'] = list()
        return self.response_data

    def parse(self, content):
        selector = etree.HTML(content)
        # Banner which contains name and info
        info = str(selector.xpath(r'//div/p/b/font/text()')[0]).strip()
        info = info.replace(info[info.find('['):info.find(']')+1], '这')
        self.response_data['info'] = info
        # The raw data is complicated, WTF!
        all_exam_data = selector.xpath(r'//div/table/td')
        exams = list()
        for i in range(0, len(all_exam_data), 8):
            info = OrderedDict()
            info['id'] = str(all_exam_data[i].xpath(r'./div/text()')[0]).strip()
            info['name'] = str(all_exam_data[i+1].xpath(r'./div/text()')[0]).strip()
            info['classno'] = str(all_exam_data[i+2].xpath(r'./div/text()')[0]).strip()
            info['teacher'] = str(all_exam_data[i+3].xpath(r'./div/text()')[0]).strip()
            info['date'] = str(all_exam_data[i+4].xpath(r'./div/text()')[0]).strip()
            info['time'] = str(all_exam_data[i+5].xpath(r'./div/text()')[0]).strip()
            info['place'] = str(all_exam_data[i+6].xpath(r'./div/text()')[0]).strip()
            info['studentno'] = str(all_exam_data[i+7].xpath(r'./div/text()')[0]).strip()
            exams.append(info)
        self.response_data['exams'] = exams
