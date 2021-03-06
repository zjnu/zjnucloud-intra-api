from django.conf.urls import patterns, url
from onecard.views import BindingView, OneCardBalanceList, OneCardDetailsList, OneCardDailyTransactionsList, \
    OneCardMonthlyTransactionsList, OneCardElectricityView

urlpatterns = patterns(
    '',
    url(r'^$', BindingView.as_view(), name='onecard_binding'),
    url(r'^(?P<username>\w+)/$', OneCardBalanceList.as_view(), name='onecard'),
    url(r'^(?P<username>\w+)/details$', OneCardDetailsList.as_view(), name='onecard_detail'),
    url(r'^(?P<username>\w+)/balance$', OneCardBalanceList.as_view(), name='onecard_balance'),
    url(r'^(?P<username>\w+)/transactions$', OneCardDailyTransactionsList.as_view(), name='onecard_daily_transaction'),
    url(r'^(?P<username>\w+)/transactions/(?P<year>\w+)/(?P<month>\w+)/$',
        OneCardMonthlyTransactionsList.as_view(), name='onecard_monthly_transaction'),
    url(r'^(?P<username>\w+)/electricity/$',
        OneCardElectricityView.as_view(), name='onecard_electricity'),
    url(r'^(?P<username>\w+)/electricity/buildings/$',
        OneCardElectricityView.as_view(), name='onecard_electricity_buildings'),
    url(r'^(?P<username>\w+)/electricity/(?P<building>[^/]+)/$',
        OneCardElectricityView.as_view(), name='onecard_electricity_buildings_building'),
    url(r'^(?P<username>\w+)/electricity/(?P<building>[^/]+)/(?P<room>.*)/',
        OneCardElectricityView.as_view(), name='onecard_electricity_buildings_building_room'),
)
