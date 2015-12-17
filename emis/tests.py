from unittest import TestCase
from emis import core


class TestCourseTable(TestCase):
    def setUp(self):
        self.course = core.CourseTable(None)

    def test_parse(self):
        f = open('../testdata.html', encoding='utf8')
        content = f.read()
        self.course.parse(content)
