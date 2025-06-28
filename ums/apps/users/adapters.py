from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from django.http import HttpRequest

class NoSignupAccountAdapter(DefaultAccountAdapter):
    """
    Custom Allauth adapter to disallow new user signups.
    """
    def is_open_for_signup(self, request: HttpRequest):
        return False