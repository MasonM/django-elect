from django.http import HttpResponseNotFound, HttpResponse
from django.conf.urls import patterns, url, include


handler404 = lambda request: HttpResponseNotFound()

urlpatterns = patterns('',
    url(r'^account/', lambda request: HttpResponse("LOGIN")),
    url(r'^election/', include('django_elect.urls')),
)

