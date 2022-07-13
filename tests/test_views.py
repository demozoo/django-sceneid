import base64
import json
from unittest.mock import patch

from django.contrib.auth import get_user
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import TestCase
import responses


class TestViews(TestCase):
    def set_up_responses(self):
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
                'redirect_uri': 'http://testsite/account/sceneid/login/'
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

        def user_data_response(request):
            expected_auth_header = "Bearer 5678567856785678"
            auth_header = request.headers['Authorization']
            if auth_header == expected_auth_header:
                return (200, {'Content-Type': 'application/json'}, json.dumps({
                    'success': True,
                    'user': {
                        'id': 1234,
                        'first_name': 'Matt', 'last_name': 'Westcott',
                        'display_name': 'gasman in a trenchcoat',
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

    @responses.activate
    @patch('sceneid.views.get_random_string')
    def test_log_in_existing_user(self, get_random_string):
        get_random_string.return_value = '66666666'
        testuser = User.objects.create_user(username='testuser', password='12345')
        testuser.sceneids.create(sceneid=1234)

        self.set_up_responses()

        response = self.client.get('/account/sceneid/auth/?next=/landing/')
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
        self.assertRedirects(response, '/landing/')
        logged_in_user = get_user(self.client)
        self.assertTrue(logged_in_user.is_authenticated)
        self.assertEqual(logged_in_user.username, 'testuser')

    @responses.activate
    @patch('sceneid.views.get_random_string')
    def test_log_in_deactivated_user(self, get_random_string):
        get_random_string.return_value = '66666666'
        testuser = User.objects.create_user(username='testuser', password='12345')
        testuser.sceneids.create(sceneid=1234)
        testuser.is_active = False
        testuser.save()

        self.set_up_responses()

        response = self.client.get('/account/sceneid/auth/?next=/landing/')
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
        self.assertRedirects(response, '/landing/')
        logged_in_user = get_user(self.client)
        self.assertFalse(logged_in_user.is_authenticated)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "This account has been deactivated.")

    @responses.activate
    @patch('sceneid.views.get_random_string')
    def test_associate_sceneid_with_existing_user(self, get_random_string):
        get_random_string.return_value = '66666666'
        testuser = User.objects.create_user(username='testuser', password='12345')

        self.set_up_responses()

        response = self.client.get('/account/sceneid/auth/?next=/landing/')
        self.assertEqual(response.status_code, 302)
        self.assertURLEqual(
            response['Location'],
            'https://id.scene.org/oauth/authorize/?state=66666666&'
            'redirect_uri=http%3A%2F%2Ftestsite%2Faccount%2Fsceneid%2Flogin%2F&'
            'response_type=code&client_id=testsite'
        )

        response = self.client.get('/account/sceneid/login/?state=66666666&code=4321432143214321')
        self.assertRedirects(response, '/account/sceneid/connect/')
        logged_in_user = get_user(self.client)
        self.assertFalse(logged_in_user.is_authenticated)

        response = self.client.get('/account/sceneid/connect/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "You successfully logged in with your SceneID as <b>gasman in a trenchcoat</b>"
        )
        self.assertContains(response, 'action="/account/sceneid/connect/old/"')
        # username in creation form should be pre-populated with cleaned version of display name
        self.assertContains(response, 'value="gasmaninatrenchcoat"')

        # post an incorrect login
        response = self.client.post('/account/sceneid/connect/old/', {
            'username': 'testuser', 'password': '12346'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter a correct username and password.")
        self.assertFalse(logged_in_user.is_authenticated)

        # post a correct login
        response = self.client.post('/account/sceneid/connect/old/', {
            'username': 'testuser', 'password': '12345'
        })
        self.assertRedirects(response, '/landing/')
        logged_in_user = get_user(self.client)
        self.assertTrue(logged_in_user.is_authenticated)
        self.assertEqual(logged_in_user.username, 'testuser')
        self.assertTrue(logged_in_user.sceneids.filter(sceneid=1234).exists())

    @responses.activate
    @patch('sceneid.views.get_random_string')
    def test_associate_sceneid_with_new_user(self, get_random_string):
        get_random_string.return_value = '66666666'
        testuser = User.objects.create_user(username='testuser', password='12345')

        self.set_up_responses()

        response = self.client.get('/account/sceneid/auth/?next=/landing/')
        self.assertEqual(response.status_code, 302)
        self.assertURLEqual(
            response['Location'],
            'https://id.scene.org/oauth/authorize/?state=66666666&'
            'redirect_uri=http%3A%2F%2Ftestsite%2Faccount%2Fsceneid%2Flogin%2F&'
            'response_type=code&client_id=testsite'
        )

        response = self.client.get('/account/sceneid/login/?state=66666666&code=4321432143214321')
        self.assertRedirects(response, '/account/sceneid/connect/')
        logged_in_user = get_user(self.client)
        self.assertFalse(logged_in_user.is_authenticated)

        response = self.client.get('/account/sceneid/connect/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "You successfully logged in with your SceneID as <b>gasman in a trenchcoat</b>"
        )
        self.assertContains(response, 'action="/account/sceneid/connect/old/"')

        # post an invalid registration form
        response = self.client.post('/account/sceneid/connect/new/', {
            'username': 'testuser'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A user with that username already exists.")
        self.assertFalse(logged_in_user.is_authenticated)

        # post a correct login
        response = self.client.post('/account/sceneid/connect/new/', {
            'username': 'testuser2'
        })
        self.assertRedirects(response, '/landing/')
        logged_in_user = get_user(self.client)
        self.assertTrue(logged_in_user.is_authenticated)
        self.assertEqual(logged_in_user.username, 'testuser2')
        self.assertTrue(logged_in_user.sceneids.filter(sceneid=1234).exists())
