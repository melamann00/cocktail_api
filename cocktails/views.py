from django.contrib.auth import authenticate, login, logout
from django.db.models import Avg
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, permissions, status, viewsets
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import CocktailFilter, IngredientFilter
from .models import Cocktail, Ingredient, Review
from .permissions import IsOwnerOrAdminOrReadOnly
from .serializers import (
    CocktailSerializer,
    IngredientSerializer,
    LoginSerializer,
    RegisterSerializer,
    ReviewSerializer,
)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class LoginView(APIView):
    """Logowanie sesyjne: po sukcesie przeglądarka/Swagger dostaje ciasteczko sesji."""

    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=LoginSerializer, responses={200: None})
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(request, **serializer.validated_data)
        if user is None:
            return Response(
                {"detail": "Nieprawidłowa nazwa użytkownika lub hasło."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        login(request, user)
        return Response({"detail": "Zalogowano.", "username": user.username, "is_admin": user.is_staff})


class LogoutView(APIView):
    @extend_schema(request=None, responses={200: None})
    def post(self, request):
        logout(request)
        return Response({"detail": "Wylogowano."})


class IngredientViewSet(viewsets.ModelViewSet):
    """Składniki: przeglądanie - każdy, dodawanie - zalogowani, edycja/usuwanie - administrator."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = IngredientFilter
    search_fields = ["name", "description"]
    ordering_fields = ["name", "id"]

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy"):
            return [permissions.IsAdminUser()]
        return super().get_permissions()


@extend_schema(
    parameters=[
        OpenApiParameter("alcoholic", bool, description="true/false - czy koktajl zawiera alkohol"),
        OpenApiParameter(
            "ingredient", str, many=True,
            description="Nazwa (fragment) lub id składnika; można podać wielokrotnie",
        ),
        OpenApiParameter("author", str, description="Nazwa użytkownika autora"),
    ]
)
class CocktailViewSet(viewsets.ModelViewSet):
    serializer_class = CocktailSerializer
    permission_classes = [IsOwnerOrAdminOrReadOnly]
    filterset_class = CocktailFilter
    search_fields = ["name", "instructions", "ingredients__name"]
    ordering_fields = ["name", "created_at", "category", "average_rating"]

    def get_queryset(self):
        return (
            Cocktail.objects.select_related("author")
            .prefetch_related("cocktail_ingredients__ingredient")
            .annotate(average_rating=Avg("reviews__rating"))
            .distinct()
            .order_by("name")
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class ReviewViewSet(viewsets.ModelViewSet):
    """Recenzje zagnieżdżone w koktajlu: /api/cocktails/{id}/reviews/"""

    serializer_class = ReviewSerializer
    permission_classes = [IsOwnerOrAdminOrReadOnly]
    filter_backends = []

    def _cocktail(self):
        try:
            return Cocktail.objects.get(pk=self.kwargs["cocktail_pk"])
        except Cocktail.DoesNotExist:
            raise NotFound("Koktajl nie istnieje.")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Review.objects.none()
        return Review.objects.filter(cocktail=self._cocktail()).select_related("user")

    def perform_create(self, serializer):
        cocktail = self._cocktail()
        if Review.objects.filter(cocktail=cocktail, user=self.request.user).exists():
            raise ValidationError({"detail": "Już dodałeś recenzję tego koktajlu."})
        serializer.save(cocktail=cocktail, user=self.request.user)
