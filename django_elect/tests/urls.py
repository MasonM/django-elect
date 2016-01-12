from django.conf.urls import *
from django.conf import settings


urlpatterns = patterns('',
    (r'^election/', include('django_elect.urls')),
    (r'^account/', 'django.contrib.auth.views.login', {
        'template_name': 'admin/login.html'
    }),
)
