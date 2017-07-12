from django.test import TestCase

from rest_framework.test import APIRequestFactory

# Create your tests here.


# Using the standard RequestFactory API to create a form POST request
factory = APIRequestFactory()

# Make an authenticated request to the view...
request = factory.get('/api/crm/orders/')
