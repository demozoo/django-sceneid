import base64
import json
from django.test import SimpleTestCase
import responses
from sceneid.client import SceneIDClient


class TestClient(SimpleTestCase):
    def setUp(self):
        self.sceneid_client = SceneIDClient('testsite', 'supersecretclientsecret')

    def test_get_authorization_uri(self):
        uri = self.sceneid_client.get_authorization_uri(
            '1234123412341234',
            'https://testsite/account/sceneid/login/',
        )
        self.assertURLEqual(
            uri,
            'https://id.scene.org/oauth/authorize/?state=1234123412341234&'
            'redirect_uri=https%3A%2F%2Ftestsite%2Faccount%2Fsceneid%2Flogin%2F&'
            'response_type=code&client_id=testsite'
        )

    def test_get_authorization_uri_with_scopes(self):
        uri = self.sceneid_client.get_authorization_uri(
            '1234123412341234',
            'https://testsite/account/sceneid/login/',
            scopes=['basic', 'user:email'],
        )
        self.assertURLEqual(
            uri,
            'https://id.scene.org/oauth/authorize/?state=1234123412341234&'
            'redirect_uri=https%3A%2F%2Ftestsite%2Faccount%2Fsceneid%2Flogin%2F&'
            'response_type=code&client_id=testsite&scope=basic+user:email'
        )

    @responses.activate
    def test_get_access_token(self):
        def token_response(request):
            expected_auth_header = (
                "Basic %s" % base64.b64encode(b'testsite:supersecretclientsecret').decode('ascii')
            )
            auth_header = request.headers['Authorization']
            if auth_header != expected_auth_header:
                raise Exception(
                    "Expected auth header %s, got %s" % (expected_auth_header, auth_header)
                )

            matcher = responses.matchers.urlencoded_params_matcher({
                'grant_type': 'authorization_code',
                'code': '4321432143214321',
                'redirect_uri': 'https://testsite/account/sceneid/login/'
            })
            if not matcher(request):
                raise Exception("Incorrect POST body: %r" % request.body)

            return (200, {'Content-Type': 'application/json'}, json.dumps({
                'access_token': '5678567856785678',
                'expires_in': 3600, 'token_type': 'Bearer', 'scope': 'basic',
                'refresh_token': '8765876587658765',
            }))

        responses.add_callback(
            responses.POST,
            url='https://id.scene.org/oauth/token/',
            callback=token_response,
        )

        response = self.sceneid_client.get_access_token(
            '4321432143214321',
            'https://testsite/account/sceneid/login/',
        )
        self.assertEqual(response['access_token'], '5678567856785678')

    @responses.activate
    def test_get_user_data(self):
        def user_data_response(request):
            expected_auth_header = "Bearer 5678567856785678"
            auth_header = request.headers['Authorization']
            if auth_header == expected_auth_header:
                return (200, {'Content-Type': 'application/json'}, json.dumps({
                    'success': True,
                    'user': {
                        'id': 1234,
                        'first_name': 'Matt', 'last_name': 'Westcott',
                        'display_name': 'gasman',
                    },
                }))
            else:
                raise Exception(
                    "Expected auth header %s, got %s" % (expected_auth_header, auth_header)
                )

        responses.add_callback(
            responses.GET,
            url='https://id.scene.org/api/3.0/me/',
            callback=user_data_response,
        )

        response = self.sceneid_client.get_user_data('5678567856785678')
        self.assertEqual(response['user']['display_name'], 'gasman')
