from django.conf.urls.defaults import patterns, url

import views


urlpatterns = patterns('django.views.generic.simple',
    (r'^success', 'direct_to_template', {'template': 'success.html'}),
) + patterns('',
    url(r'^statistics', views.statistics),
    url(r'^spreadsheet', views.generate_spreadsheet),
    url(r'^disassociate/(?P<id>\d+)?', views.disassociate_accounts),
    url(r'', views.vote),
)
