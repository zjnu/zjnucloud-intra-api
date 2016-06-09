from django.conf.urls import patterns, url
from onecard.views import BindingView, OneCardBalanceList, OneCardDetailsList

urlpatterns = patterns(
    '',
    url(r'^$', BindingView.as_view(), name='onecard_binding'),
    url(r'^(?P<username>\w+)/$', OneCardBalanceList.as_view(), name='onecard'),
    url(r'^(?P<username>\w+)/details$', OneCardDetailsList.as_view(), name='onecard_detail'),
    url(r'^(?P<username>\w+)/balance$', OneCardBalanceList.as_view(), name='onecard_balance'),
)
