from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

class MatcherViewsTest(TestCase):
    
    def setUp(self):
        # Create and log in user
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.client.login(username='testuser', password='password123')
        
    def test_matcher_api_view(self):
        url = reverse('match-resumes')  # This should match the name used in matcher/urls.py
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/json', response['Content-Type'])