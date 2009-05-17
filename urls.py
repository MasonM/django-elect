import sys

from django.conf.urls.defaults import patterns, include
from django.conf import settings
from django.contrib import admin


admin.autodiscover()
admin.site.index_template = "admin/admin_index.html"

urlpatterns = patterns('',
    (r'^admin/(.*)', admin.site.root),
    (r'^admin_docs/', include('django.contrib.admindocs.urls')),
    (r'^election/', include('election.apps.django-elect.urls')),
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
)

#allow static serve only for development work using the command
#./manage.py runserver
if hasattr(sys, "argv") and 'runserver' in sys.argv:
    urlpatterns += patterns('',
        (r'^media/(.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
            'show_indexes': True}),
    )
