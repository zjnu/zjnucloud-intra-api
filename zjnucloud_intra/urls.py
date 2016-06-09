from django.conf.urls import include, url
from django.contrib import admin

from common import views

admin.autodiscover()

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^emis/', include('emis.binding.urls')),
    url(r'^emis/', include('emis.urls')),
    url(r'^onecard/', include('onecard.urls')),
    url(r'^docs/', include('rest_framework_docs.urls')),
]
