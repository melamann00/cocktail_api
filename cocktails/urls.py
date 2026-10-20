from rest_framework.routers import DefaultRouter
from django.urls import include, path

from .views import CocktailViewSet, IngredientViewSet, ReviewViewSet

router = DefaultRouter()
router.register("ingredients", IngredientViewSet, basename="ingredient")
router.register("cocktails", CocktailViewSet, basename="cocktail")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "cocktails/<int:cocktail_pk>/reviews/",
        ReviewViewSet.as_view({"get": "list", "post": "create"}),
        name="cocktail-reviews",
    ),
    path(
        "cocktails/<int:cocktail_pk>/reviews/<int:pk>/",
        ReviewViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}),
        name="cocktail-review-detail",
    ),
]
