from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import login as auth_login
from django.core.exceptions import SuspiciousOperation
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.crypto import get_random_string

from sceneid.client import SceneIDClient


def _get_sceneid_client():
    return SceneIDClient(
        settings.SCENEID_CLIENT_ID,
        settings.SCENEID_CLIENT_SECRET,
        getattr(settings, 'SCENEID_HOSTNAME', 'id.scene.org'),
    )


def _get_return_uri():
    return settings.BASE_URL + reverse('sceneid:login')


def auth_redirect(request):
    """
    Generate the SceneID auth redirect URL and send user there.
    """
    client = _get_sceneid_client()
    state = get_random_string(length=32)

    redirect_uri = client.get_authorization_uri(state, _get_return_uri())
    request.session['sceneid_state'] = state
    return redirect(redirect_uri)


def login(request):
    """
    Process the SceneID Oauth response
    """
    state = request.GET['state']
    code = request.GET['code']

    if (state != request.session['sceneid_state']):
        raise SuspiciousOperation("State mismatch!")

    client = _get_sceneid_client()
    token_data = client.get_access_token(code, _get_return_uri())
    access_token = token_data['access_token']
    request.session['sceneid_accesstoken'] = access_token
    user_data = client.get_user_data(access_token)

    sceneid = user_data["user"]["id"]
    # look for an existing user linked to this sceneid
    User = get_user_model()
    try:
        user = User.objects.get(sceneids__sceneid=sceneid)
    except User.DoesNotExist:
        user = None

    if user:
        auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect(settings.LOGIN_REDIRECT_URL)
    else:
        return HttpResponse(repr(user_data))
