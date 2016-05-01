from django.conf.urls import patterns, url

from django_elect import views, autocomplete


urlpatterns = patterns('',
    url(r'^biographies', views.biographies, name="django_elect_biographies"),
    url(r'^success', views.success, name="django_elect_success"),
    url(r'^statistics/(?P<id>\d+)', views.statistics,
        name="django_elect_stats"),
    url(r'^spreadsheet/(?P<id>\d+)', views.generate_spreadsheet,
        name="django_elect_spreadsheet"),
    url(r'^disassociate/(?P<id>\d+)', views.disassociate_accounts,
        name="django_elect_disassociate"),
    url(r'^vote-plurality-autocomplete/$',
        autocomplete.CandidateAutocomplete.as_view(ballot_type="Pl"),
        name='vote-plurality-autocomplete'),
    url(r'^vote-preferential-autocomplete/$',
        autocomplete.CandidateAutocomplete.as_view(ballot_type="Pr"),
        name='vote-preferential-autocomplete'),
    url(r'^account-autocomplete/$',
        autocomplete.AccountAutocomplete.as_view(),
        name='account-autocomplete'),
    url(r'', views.vote, name="django_elect_vote"),
)
