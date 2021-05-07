from django.test import TestCase
from unittest.mock import patch


class TestViews(TestCase):
    @patch('sceneid.views.get_random_string')
    def test_auth_redirect(self, get_random_string):
        get_random_string.return_value = '66666666'
        response = self.client.get('/account/sceneid/auth/?next=/music/')
        self.assertEqual(response.status_code, 302)
        self.assertURLEqual(
            response['Location'],
            'https://id.scene.org/oauth/authorize/?state=66666666&'
            'redirect_uri=http%3A%2F%2Ftestsite%2Faccount%2Fsceneid%2Flogin%2F&'
            'response_type=code&client_id=testsite'
        )
