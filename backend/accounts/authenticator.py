from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings
from rest_framework.authentication import CSRFCheck
from rest_framework.exceptions import AuthenticationFailed


def enforce_csrf(request):
    """
    Enforce CSRF validation for cookie-based authentication.
    """
    def dummy_get_response(request):
        return None

    check = CSRFCheck(get_response=dummy_get_response)
    check.process_request(request)
    reason = check.process_view(request, None, (), {})

    if reason:
        raise AuthenticationFailed(f'CSRF Failed: {reason}')


class CustomCookieJWTAuthenticator(JWTAuthentication):
    """
    JWT authenticator that supports cookie-based authentication with optional CSRF protection.
    Controlled by AUTH_CSRF_AUTHENTICATION in environment.
    """

    def authenticate(self, request):
        # Determine token source: cookie or header
        header = self.get_header(request)
        raw_token = self.get_raw_token(header) if header else request.COOKIES.get(settings.SIMPLE_JWT["AUTH_COOKIE"])

        if not raw_token:
            return None

        validated_token = self.get_validated_token(raw_token)

        # Only enforce CSRF for unsafe methods and if enabled
        enable_csrf_auth = getattr(settings, "AUTH_CSRF_AUTHENTICATION", False)
        if enable_csrf_auth and request.method not in ["GET", "HEAD", "OPTIONS"]:
            enforce_csrf(request)

        return self.get_user(validated_token), validated_token
