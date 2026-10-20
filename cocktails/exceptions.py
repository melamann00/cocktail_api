from django.db.models import ProtectedError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    if isinstance(exc, ProtectedError):
        return Response(
            {"detail": "Nie można usunąć: obiekt jest używany przez inne zasoby (np. koktajle)."},
            status=status.HTTP_409_CONFLICT,
        )
    return exception_handler(exc, context)
