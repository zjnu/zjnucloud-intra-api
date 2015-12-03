from collections import OrderedDict
from io import BytesIO

from django.utils.datastructures import MultiValueDictKeyError
import requests
from PIL import Image
from lxml import etree

from emis import ocr

__author__ = 'ddmax'

# EMIS_URL
URL_LOGIN = 'http://10.1.68.13:8001/login.asp'
URL_LOGOUT = 'http://10.1.68.13:8001/loginOut.asp'
URL_CODE = 'http://10.1.68.13:8001/checkcode.asp'
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
STATUS_ERR_CODE = 3  # Captcha invalid
STATUS_ERR_EMIS = 4  # EMIS error

# Messages
MSG_ERR_PARAM = '参数错误'
MSG_ERR_UNKNOWN = '未知错误'
MSG_SUCCESS = ''  # Login success
MSG_ERR_USERNAME = '账号不存在哦，请检查账号是否输入正确。'  # Username invalid
MSG_ERR_PASSWORD = '您的密码输错了呢，请检查。'  # Password invalid
MSG_ERR_CODE = '我们的服务器出现了异常，程序猿正在玩命抢修中。。。'  # Captcha invalid
MSG_ERR_EMIS = '教务系统暂时无法访问了，过会儿再访问吧！'  # EMIS error


def init(username, password, usertype='student'):
    session = Session(username, password, usertype)
    status, message = session.login()
    return session, status, message


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
        # Request times at least 10
        request_times = 0
        while self.result_code != 200 and request_times < 10:
            request_times += 1
            print('Attempt to get checkcode...')
            # Fetch captcha
            codeimg = self.get(URL_CODE)
            imgbytes = codeimg.content
            # Recognize the captcha
            image = Image.open(BytesIO(imgbytes))
            code = ocr.ocr_captcha(image)
            print('Checkcode is ' + code)
            # with open('code.bmp', 'wb') as f:
            #     f.write(imgbytes)
            # code = input('Please input code:')
            # Post data
            data = {
                'radioUserType': self.usertype,
                'userId': self.username,
                'pwd': self.password,
                'GetCode': code,
            }
            result = self.post(URL_LOGIN, data=data)
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
            elif content.find('验证码输入错误') != -1:
                return STATUS_ERR_CODE, MSG_ERR_CODE
            else:
                return STATUS_SUCCESS, MSG_SUCCESS
        return STATUS_ERR_EMIS, MSG_ERR_EMIS

    def logout(self,):
        self.get(URL_LOGOUT)
        self.close()


class EmisBase:

    def __init__(self, request):
        self.response_data = OrderedDict()
        try:
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
            total_score = self.session.post(URL_TOTALSCORE)
            total_score.encoding = 'gbk'
            content = total_score.content.decode('gbk')
            # with open('termscore.html', 'wb') as f:
            #     f.write(content)
            # Parse the data with xpath
            self.parse(content)
            # Log out
            self.session.logout()
            print('Logged out!')
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
            params = '?year=' + year \
                     + '&nouse=' + str(int(year) + 1) \
                     + '&select=' + semester
            courses = self.session.get(URL_COURSETABLE + params)
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
            info['no'] = str(each.xpath(r'./td/text()')[0]).strip()
            info['id'] = str(each.xpath(r'./td/text()')[1]).strip()
            info['name'] = str(each.xpath(r'./td/text()')[2]).strip()
            info['teacher'] = str(each.xpath(r'./td/text()')[3]).strip()
            info['time'] = str(each.xpath(r'./td/div/text()')[0]).strip()
            info['classroom'] = str(each.xpath(r'./td/text()')[6]).strip()
            info['total'] = str(each.xpath(r'./td/text()')[7]).strip()
            info['elected'] = str(each.xpath(r'./td/text()')[8]).strip()
            info['credit'] = str(each.xpath(r'./td/text()')[9]).strip()
            info['property'] = str(each.xpath(r'./td/text()')[10]).strip()
            info['remarks'] = str(each.xpath(r'./td/text()')[11]).strip()
            courses.append(info)
        self.response_data['courses'] = courses


class Exam(EmisBase):

    def __init__(self, request):
        super().__init__(request)

    def get_exam_schedule(self):
        # If login success, get scores
        if self.status == STATUS_SUCCESS:
            exams = self.session.get(URL_EXAMSCHEDULE)
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
