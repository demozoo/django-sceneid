from django.urls import include, path

urlpatterns = [
    path('account/sceneid/', include('sceneid.urls')),
]
