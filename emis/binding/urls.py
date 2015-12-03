from django.conf.urls import patterns, url

from .views import BindingView

urlpatterns = patterns(
    '',
    url(r'^binding/', BindingView.as_view(), name='rest_binding'),
)
