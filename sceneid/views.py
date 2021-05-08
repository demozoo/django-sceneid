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
from django.views import View

from sceneid.client import SceneIDClient
from sceneid.forms import UserCreationForm
from sceneid.models import SceneID


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


class ConnectView(View):
    """
    Display the login / registration forms for associating a SceneID we haven't seen before
    with an existing or new account
    """
    def get(self, request):
        if not request.session.get('sceneid_login_user_data'):
            return _redirect_back(request)

        login_form = AuthenticationForm(request)
        register_form = UserCreationForm()

        return render(request, 'sceneid/connect.html', {
            'display_name': request.session['sceneid_login_user_data']['display_name'],
            'login_form': login_form,
            'register_form': register_form,
        })


class ConnectOldView(View):
    """
    Handle form submissions of the login form for associating a SceneID with an existing account
    """
    def dispatch(self, request):
        if not request.session.get('sceneid_login_user_data'):
            return _redirect_back(request)

        if not request.method == 'POST':
            return redirect('sceneid:connect')

        login_form = AuthenticationForm(request, request.POST)
        if login_form.is_valid():
            user = login_form.get_user()
            sceneid_num = request.session['sceneid_login_user_data']['id']
            SceneID.objects.get_or_create(sceneid=sceneid_num, defaults={'user': user})
            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            try:
                del request.session['sceneid_login_user_data']
            except KeyError:
                # login will overwrite request.session if the old session was authenticated
                pass

            return _redirect_back(request)
        else:
            register_form = UserCreationForm()
            return render(request, 'sceneid/connect.html', {
                'display_name': request.session['sceneid_login_user_data']['display_name'],
                'login_form': login_form,
                'register_form': register_form,
            })


class ConnectNewView(View):
    """
    Handle form submissions of the registration form for associating a SceneID with a new account
    """
    def dispatch(self, request):
        if not request.session.get('sceneid_login_user_data'):
            return _redirect_back(request)

        if not request.method == 'POST':
            return redirect('sceneid:connect')

        register_form = UserCreationForm(request.POST)
        if register_form.is_valid():
            user = register_form.save()
            sceneid_num = request.session['sceneid_login_user_data']['id']
            SceneID.objects.get_or_create(sceneid=sceneid_num, defaults={'user': user})
            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            try:
                del request.session['sceneid_login_user_data']
            except KeyError:
                # login will overwrite request.session if the old session was authenticated
                pass

            return _redirect_back(request)
        else:
            login_form = AuthenticationForm(request)
            return render(request, 'sceneid/connect.html', {
                'display_name': request.session['sceneid_login_user_data']['display_name'],
                'login_form': login_form,
                'register_form': register_form,
            })
