import base64
import json
from unittest.mock import patch

from django.contrib.auth import get_user
from django.contrib.auth.models import User
from django.test import TestCase
import responses


class TestViews(TestCase):
    @responses.activate
    @patch('sceneid.views.get_random_string')
    def test_log_in_existing_user(self, get_random_string):
        get_random_string.return_value = '66666666'
        testuser = User.objects.create_user(username='testuser', password='12345')
        testuser.sceneids.create(sceneid=1234)

        def token_response(request):
            expected_auth_header = (
                "Basic %s" % base64.b64encode(b'testsite:supersecretclientsecret').decode('ascii')
            )
            auth_header = request.headers['Authorization']
            if auth_header != expected_auth_header:
                raise Exception(
                    "Expected auth header %s, got %s" % (expected_auth_header, auth_header)
                )

            matcher = responses.urlencoded_params_matcher({
                'grant_type': 'authorization_code',
                'code': '4321432143214321',
                'redirect_uri': 'http://testsite/account/sceneid/login/'
            })
            if not matcher(request.body):
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

        response = self.client.get('/account/sceneid/auth/?next=/music/')
        self.assertEqual(response.status_code, 302)
        self.assertURLEqual(
            response['Location'],
            'https://id.scene.org/oauth/authorize/?state=66666666&'
            'redirect_uri=http%3A%2F%2Ftestsite%2Faccount%2Fsceneid%2Flogin%2F&'
            'response_type=code&client_id=testsite'
        )

        # attempt to return with mismatched state
        response = self.client.get('/account/sceneid/login/?state=55555555&code=4321432143214321')
        self.assertEqual(response.status_code, 400)

        # now with correct state
        response = self.client.get('/account/sceneid/login/?state=66666666&code=4321432143214321')
        self.assertRedirects(response, '/')
        logged_in_user = get_user(self.client)
        self.assertTrue(logged_in_user.is_authenticated)
        self.assertEqual(logged_in_user.username, 'testuser')
