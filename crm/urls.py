from django.conf.urls import include, url
from rest_framework import routers
from crm_app.api import *

from django.contrib import admin
admin.autodiscover()
router=routers.DefaultRouter()
url(r'^api/crm/', include('crm_app.urls')),

urlpatterns = (
    # Examples:
    # url(r'^$', 'crm.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
)
