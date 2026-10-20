from rest_framework.authentication import SessionAuthentication


class SessionAuthentication401(SessionAuthentication):
    """Sesja Django, ale brak logowania daje 401 (a nie 403) i bez okienka przeglądarki."""

    def authenticate_header(self, request):
        return "Session"
