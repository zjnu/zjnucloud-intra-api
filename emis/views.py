import datetime
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from emis.models import EmisUser

from emis.serializers import BaseEmisSerializer
import emis.core as core


class ScoreList(APIView):
    allowed_methods = ('POST', 'OPTIONS', 'HEAD')

    def post(self, request, format=None):
        """
        List all scores of user
        """
        emis_user = EmisUser.objects.get(username=request.data.get('username'))
        if self.should_use_cache(emis_user):
            return Response(json.loads(emis_user.scores))
        else:
            data = core.Score(request).get_total_score()
            serializer = BaseEmisSerializer(data)
            return Response(serializer.data)

    @staticmethod
    def should_use_cache(emis_user):
        if emis_user.scores_last_update is not None \
           and datetime.datetime.now() - emis_user.scores_last_update < datetime.timedelta(minutes=2):
            return True
        else:
            return False


class CourseTableList(APIView):
    allowed_methods = ('POST', 'OPTIONS', 'HEAD')

    def post(self, request, year=None, semester=None, format=None):
        """
        List course table by year and semester
        """
        if year is None or semester is None:
            year, semester = self.populate_current_semester()
        data = core.CourseTable(request).get_course_table(year, semester)
        serializer = BaseEmisSerializer(data)
        return Response(serializer.data)

    def populate_current_semester(self, ):
        now = datetime.datetime.now()
        current_year = now.year
        current_month = now.month
        if 1 < current_month < 6:
            current_year -= 1
            semester = 2
        else:
            semester = 1
        return str(current_year), str(semester)


class ExamScheduleList(APIView):
    allowed_methods = ('POST', 'OPTIONS', 'HEAD')

    def post(self, request, format=None):
        """
        List course table by year and semester
        """
        data = core.Exam(request).get_exam_schedule()
        serializer = BaseEmisSerializer(data)
        return Response(serializer.data)
