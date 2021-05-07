from django.conf import settings
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


def auth_redirect(request):
    client = _get_sceneid_client()
    return_uri = settings.BASE_URL + reverse('sceneid:login')
    state = get_random_string(length=32)

    redirect_uri = client.get_authorization_uri(state, return_uri)
    request.session['sceneid_state'] = state
    return redirect(redirect_uri)


def login(request):
    pass
