from django.urls import path

from sceneid import views

app_name = 'sceneid'

urlpatterns = [
    path('auth/', views.AuthRedirectView.as_view(), {}, 'auth'),
    path('login/', views.LoginView.as_view(), {}, 'login'),
    path('connect/', views.ConnectView.as_view(), {}, 'connect'),
    path('connect/old/', views.ConnectOldView.as_view(), {}, 'connect_old'),
    path('connect/new/', views.ConnectNewView.as_view(), {}, 'connect_new'),
]
