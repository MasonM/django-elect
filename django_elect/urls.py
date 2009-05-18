from django.conf.urls.defaults import patterns, url

from django_elect import views, settings


urlpatterns = patterns('django.views.generic.simple',
    (r'^success', 'direct_to_template', {
        'template': 'django_elect/success.html',
        'extra_context': {
            'DJANGO_ELECT_MEDIA_ROOT': settings.DJANGO_ELECT_MEDIA_ROOT,
        },
    }),
) + patterns('',
    url(r'^biographies', views.biographies),
    url(r'^statistics/(?P<id>\d+)', views.statistics),
    url(r'^spreadsheet/(?P<id>\d+)', views.generate_spreadsheet),
    url(r'^disassociate/(?P<id>\d+)', views.disassociate_accounts),
    url(r'', views.vote),
)
