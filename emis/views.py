from rest_framework.views import APIView
from rest_framework.response import Response

from emis.serializers import BaseEmisSerializer
import emis.core as core


class ScoreList(APIView):
    allowed_methods = ('POST', 'OPTIONS', 'HEAD')

    def post(self, request, format=None):
        """
        List all scores of user
        """
        data = core.Score(request).get_total_score()
        serializer = BaseEmisSerializer(data)
        return Response(serializer.data)


class CourseTableList(APIView):
    allowed_methods = ('POST', 'OPTIONS', 'HEAD')

    def post(self, request, year, semester, format=None):
        """
        List course table by year and semester
        """
        data = core.CourseTable(request).get_course_table(year, semester)
        serializer = BaseEmisSerializer(data)
        return Response(serializer.data)


class ExamScheduleList(APIView):
    allowed_methods = ('POST', 'OPTIONS', 'HEAD')

    def post(self, request, format=None):
        """
        List course table by year and semester
        """
        data = core.Exam(request).get_exam_schedule()
        serializer = BaseEmisSerializer(data)
        return Response(serializer.data)
