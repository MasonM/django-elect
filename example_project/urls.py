from django.conf.urls.defaults import patterns, include
from django.conf import settings
from django.contrib import admin


admin.autodiscover()


urlpatterns = patterns('',
    (r'^admin/(.*)', admin.site.root),
    (r'^admin_docs/', include('django.contrib.admindocs.urls')),
    (r'^election/', include('django_elect.urls')),
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
)

#allow static serve only for development work 
if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
            'show_indexes': True}),
    )
