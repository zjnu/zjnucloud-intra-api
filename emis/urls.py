from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from emis.views import ScoreList, CourseTableList, ExamScheduleList

urlpatterns = [
    url(r'^score/$', ScoreList.as_view(), name='score'),
    url(r'^course/$', CourseTableList.as_view(), name='course'),
    url(r'^course/(\d+)/(\d+)/$', CourseTableList.as_view(), name='course'),
    url(r'^exam/$', ExamScheduleList.as_view(), name='exam'),
]

urlpatterns = format_suffix_patterns(urlpatterns)
