import urllib

import requests


class SceneIDClient:
    def __init__(self, client_id, client_secret, hostname='id.scene.org'):
        self.client_id = client_id
        self.client_secret = client_secret
        self.hostname = hostname

    def get_authorization_uri(self, state, redirect_uri, scopes=None):
        params = {
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'state': state,
        }
        if scopes:
            params['scope'] = ' '.join(scopes)

        return "https://%s/oauth/authorize/?%s" % (
            self.hostname,
            urllib.parse.urlencode(params)
        )

    def get_access_token(self, code, redirect_uri):
        url = "https://%s/oauth/token/" % self.hostname
        response = requests.post(
            url,
            data={
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': redirect_uri,
            },
            auth=(self.client_id, self.client_secret),
        )
        return response.json()

    def get_user_data(self, access_token):
        url = "https://%s/api/3.0/me/" % self.hostname
        response = requests.get(
            url,
            headers={'Authorization': "Bearer %s" % access_token}
        )
        return response.json()
