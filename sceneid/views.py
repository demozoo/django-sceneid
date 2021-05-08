from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import login as auth_login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.core.exceptions import SuspiciousOperation
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.module_loading import import_string
from django.views import View
from django.views.generic import TemplateView
from django.views.generic.base import ContextMixin, TemplateResponseMixin

from sceneid.client import SceneIDClient
from sceneid.forms import UserCreationForm
from sceneid.models import SceneID


app_config = apps.get_app_config('sceneid')


def _get_sceneid_client():
    return SceneIDClient(
        settings.SCENEID_CLIENT_ID,
        settings.SCENEID_CLIENT_SECRET,
        getattr(settings, 'SCENEID_HOSTNAME', 'id.scene.org'),
    )


def _get_return_uri():
    return settings.BASE_URL + reverse('sceneid:login')


def _redirect_back(request):
    next_url = request.session.get('sceneid_next_url')
    next_url_is_valid = (
        next_url
        and url_has_allowed_host_and_scheme(next_url, request.get_host(), request.is_secure())
    )
    if not next_url_is_valid:
        next_url = settings.LOGIN_REDIRECT_URL
    return redirect(next_url)


class AuthRedirectView(View):
    """
    Generate the SceneID auth redirect URL and send user there.
    """
    def get(self, request):
        client = _get_sceneid_client()
        state = get_random_string(length=32)

        redirect_uri = client.get_authorization_uri(state, _get_return_uri())
        request.session['sceneid_state'] = state
        request.session['sceneid_next_url'] = request.GET.get('next')
        return redirect(redirect_uri)


class LoginView(View):
    """
    Process the SceneID Oauth response
    """
    def get(self, request):
        state = request.GET['state']
        code = request.GET['code']

        if (state != request.session['sceneid_state']):
            raise SuspiciousOperation("State mismatch!")

        client = _get_sceneid_client()
        token_data = client.get_access_token(code, _get_return_uri())
        access_token = token_data['access_token']
        request.session['sceneid_access_token'] = access_token
        user_data = client.get_user_data(access_token)

        sceneid = user_data["user"]["id"]
        # look for an existing user linked to this sceneid
        User = get_user_model()
        try:
            user = User.objects.get(sceneids__sceneid=sceneid)
        except User.DoesNotExist:
            user = None

        if user:
            if user.is_active:
                auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            else:
                messages.error(request, "This account has been deactivated.")

            return _redirect_back(request)
        else:
            # no known user with this sceneid - prompt them to connect to a new or existing account
            request.session['sceneid_login_user_data'] = user_data["user"]
            return redirect('sceneid:connect')


class ConnectView(TemplateView):
    """
    Display the login / registration forms for associating a SceneID we haven't seen before
    with an existing or new account
    """
    template_name = app_config.connect_template_name
    login_form_class = import_string(app_config.connect_login_form_class)
    register_form_class = import_string(app_config.connect_register_form_class)

    def get(self, request, *args, **kwargs):
        try:
            self.user_data = request.session['sceneid_login_user_data']
        except KeyError:
            return _redirect_back(request)

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        login_form = self.login_form_class(self.request)
        register_form = self.register_form_class(self.user_data)

        context.update({
            'user_data': self.user_data,
            'login_form': login_form,
            'register_form': register_form,
        })
        return context


class ConnectOldView(TemplateResponseMixin, ContextMixin, View):
    """
    Handle form submissions of the login form for associating a SceneID with an existing account
    """
    template_name = app_config.connect_template_name
    login_form_class = import_string(app_config.connect_login_form_class)
    register_form_class = import_string(app_config.connect_register_form_class)

    def dispatch(self, request):
        try:
            self.user_data = request.session['sceneid_login_user_data']
        except KeyError:
            return _redirect_back(request)

        if not request.method == 'POST':
            return redirect('sceneid:connect')

        self.login_form = self.login_form_class(request, request.POST)
        if self.login_form.is_valid():
            return self.form_valid(self.login_form)
        else:
            return self.form_invalid(self.login_form)

    def form_valid(self, form):
        user = form.get_user()
        SceneID.objects.get_or_create(sceneid=self.user_data['id'], defaults={'user': user})
        auth_login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
        try:
            del self.request.session['sceneid_login_user_data']
        except KeyError:
            # login will overwrite request.session if the old session was authenticated
            pass

        return _redirect_back(self.request)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data())

    def get_context_data(self):
        context = super().get_context_data()

        register_form = self.register_form_class(self.user_data)

        context.update({
            'user_data': self.user_data,
            'login_form': self.login_form,
            'register_form': register_form,
        })

        return context


class ConnectNewView(TemplateResponseMixin, ContextMixin, View):
    """
    Handle form submissions of the registration form for associating a SceneID with a new account
    """
    template_name = app_config.connect_template_name
    login_form_class = import_string(app_config.connect_login_form_class)
    register_form_class = import_string(app_config.connect_register_form_class)

    def dispatch(self, request):
        try:
            self.user_data = request.session['sceneid_login_user_data']
        except KeyError:
            return _redirect_back(request)

        if not request.method == 'POST':
            return redirect('sceneid:connect')

        self.register_form = self.register_form_class(self.user_data, request.POST)
        if self.register_form.is_valid():
            return self.form_valid(self.register_form)
        else:
            return self.form_invalid(self.register_form)

    def form_valid(self, form):
        user = form.save()
        SceneID.objects.get_or_create(sceneid=self.user_data['id'], defaults={'user': user})
        auth_login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
        try:
            del self.request.session['sceneid_login_user_data']
        except KeyError:
            # login will overwrite request.session if the old session was authenticated
            pass

        return _redirect_back(self.request)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data())

    def get_context_data(self):
        context = super().get_context_data()

        login_form = self.login_form_class(self.request)

        context.update({
            'user_data': self.user_data,
            'login_form': login_form,
            'register_form': self.register_form,
        })

        return context
