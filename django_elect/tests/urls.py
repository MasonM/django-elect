from django.conf.urls.defaults import *


urlpatterns = patterns('',
    (r'^election/', include('django_elect.urls')),
    (r'^accounts/login/', 'django.contrib.auth.views.login', {
        'template_name': 'admin/login.html'
    }),
)
