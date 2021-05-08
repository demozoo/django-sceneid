from django.apps import AppConfig


class SceneIDConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sceneid'

    connect_template_name = 'sceneid/connect.html'
    connect_login_form_class = 'django.contrib.auth.forms.AuthenticationForm'
    connect_register_form_class = 'sceneid.forms.UserCreationForm'
