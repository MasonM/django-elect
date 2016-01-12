from django.conf.urls import *
from django.contrib import admin


admin.autodiscover()


urlpatterns = patterns('',
    (r'^admin/(.*)', admin.site.root),
    (r'^admin_docs/', include('django.contrib.admindocs.urls')),
    (r'^election/', include('django_elect.urls')),
    (r'^account/', 'django.contrib.auth.views.login', {
        'template_name': 'admin/login.html'
    }),
)
