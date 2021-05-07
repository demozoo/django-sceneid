from django.http import HttpResponse
from django.urls import include, path


def home_view(request):
    return HttpResponse('home')


urlpatterns = [
    path('', home_view),
    path('account/sceneid/', include('sceneid.urls')),
]
