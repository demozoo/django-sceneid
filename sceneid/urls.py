from django.urls import path

from sceneid import views

app_name = 'sceneid'

urlpatterns = [
    path('auth/', views.auth_redirect, {}, 'auth'),
    path('login/', views.login, {}, 'login'),
]
