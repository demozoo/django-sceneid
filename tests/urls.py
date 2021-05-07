from django.http import HttpResponse
from django.urls import include, path


def home_view(request):
    return HttpResponse('home')


def landing_view(request):
    return HttpResponse('landing page')


urlpatterns = [
    path('', home_view),
    path('landing/', landing_view),
    path('account/sceneid/', include('sceneid.urls')),
]
