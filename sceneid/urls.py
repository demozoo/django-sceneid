from django.urls import path

from sceneid import views

app_name = 'sceneid'

urlpatterns = [
    path('auth/', views.auth_redirect, {}, 'auth'),
    path('login/', views.login, {}, 'login'),
    path('connect/', views.connect, {}, 'connect'),
    path('connect/old/', views.connect_old, {}, 'connect_old'),
    path('connect/new/', views.connect_new, {}, 'connect_new'),
]
