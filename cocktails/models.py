from decimal import Decimal
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Ingredient(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_alcoholic = models.BooleanField(default=False)
    image_url = models.URLField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Cocktail(models.Model):
    name = models.CharField(max_length=150, unique=True)
    category = models.CharField(max_length=60, db_index=True)
    instructions = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="cocktails",
    )
    ingredients = models.ManyToManyField(
        Ingredient, through="CocktailIngredient", related_name="cocktails"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class CocktailIngredient(models.Model):
    """Tabela pośrednia: ilość danego składnika w koktajlu."""

    class Unit(models.TextChoices):
        ML = "ml", "ml"
        CL = "cl", "cl"
        G = "g", "g"
        TSP = "tsp", "łyżeczka"
        TBSP = "tbsp", "łyżka"
        DASH = "dash", "dash"
        PIECE = "piece", "sztuka"
        SLICE = "slice", "plasterek"
        LEAF = "leaf", "listek"

    cocktail = models.ForeignKey(
        Cocktail, on_delete=models.CASCADE, related_name="cocktail_ingredients"
    )
    # PROTECT: nie można usunąć składnika, który jest używany w koktajlu.
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.PROTECT, related_name="cocktail_ingredients"
    )
    quantity = models.DecimalField(
        max_digits=7, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    unit = models.CharField(max_length=10, choices=Unit.choices, default=Unit.ML)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cocktail", "ingredient"], name="unique_ingredient_per_cocktail"
            )
        ]

    def __str__(self):
        return f"{self.quantity} {self.unit} {self.ingredient}"


class Review(models.Model):
    cocktail = models.ForeignKey(Cocktail, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews"
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["cocktail", "user"], name="one_review_per_user")
        ]
