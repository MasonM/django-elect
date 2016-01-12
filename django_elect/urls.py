from django.conf.urls import patterns, url

from django_elect import views


urlpatterns = patterns('',
    url(r'^biographies', views.biographies, name="django_elect_biographies"),
    url(r'^success', views.success, name="django_elect_success"),
    url(r'^statistics/(?P<id>\d+)', views.statistics,
        name="django_elect_stats"),
    url(r'^spreadsheet/(?P<id>\d+)', views.generate_spreadsheet,
        name="django_elect_spreadsheet"),
    url(r'^disassociate/(?P<id>\d+)', views.disassociate_accounts,
        name="django_elect_disassociate"),
    url(r'', views.vote, name="django_elect_vote"),
)
