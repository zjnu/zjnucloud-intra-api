from django.conf.urls import patterns, url
from onepay.views import BindingView

urlpatterns = patterns(
    '',
    url(r'^binding/$', BindingView.as_view(), name='onepay_binding'),
    url(r'^binding/$', BindingView.as_view(), name='onepay_binding'),
)
