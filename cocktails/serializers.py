from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from .models import Cocktail, CocktailIngredient, Ingredient, Review

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]
        extra_kwargs = {"email": {"required": True}}

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Użytkownik z tym adresem e-mail już istnieje.")
        return value

    def validate(self, attrs):
        validate_password(attrs["password"], User(username=attrs["username"], email=attrs["email"]))
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ["id", "name", "description", "type", "percentage", "is_alcoholic", "image_url"]

    def validate_name(self, value):
        value = value.strip()
        qs = Ingredient.objects.filter(name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Składnik o tej nazwie już istnieje.")
        return value

class CocktailIngredientReadSerializer(serializers.ModelSerializer):
    ingredient = IngredientSerializer(read_only=True)

    class Meta:
        model = CocktailIngredient
        fields = ["ingredient", "measure"]

class CocktailIngredientWriteSerializer(serializers.Serializer):
    ingredient = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    measure = serializers.CharField(max_length=100, allow_blank=True, default="")

class CocktailSerializer(serializers.ModelSerializer):
    ingredients = CocktailIngredientWriteSerializer(many=True, write_only=True)
    recipe = CocktailIngredientReadSerializer(
        source="cocktail_ingredients", many=True, read_only=True
    )
    author = serializers.StringRelatedField(read_only=True)
    is_alcoholic = serializers.SerializerMethodField()
    average_rating = serializers.FloatField(read_only=True, default=None)

    class Meta:
        model = Cocktail
        fields = [
            "id", "name", "category", "glass", "tags", "instructions", "image_url",
            "ingredients", "recipe",
            "is_alcoholic", "average_rating", "author", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_is_alcoholic(self, obj) -> bool:
        return any(ci.ingredient.is_alcoholic for ci in obj.cocktail_ingredients.all())

    def validate_name(self, value):
        value = value.strip()
        qs = Cocktail.objects.filter(name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Koktajl o tej nazwie już istnieje.")
        return value

    def validate_category(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Kategoria nie może być pusta.")
        return value

    def validate_tags(self, value):
        if not isinstance(value, list) or not all(isinstance(t, str) and t.strip() for t in value):
            raise serializers.ValidationError("Tagi muszą być niepustymi napisami.")
        return value

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError("Koktajl musi mieć co najmniej jeden składnik.")
        ids = [item["ingredient"].pk for item in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError("Składniki nie mogą się powtarzać.")
        return value

    @staticmethod
    def _save_ingredients(cocktail, items):
        CocktailIngredient.objects.bulk_create(
            CocktailIngredient(cocktail=cocktail, **item) for item in items
        )

    @transaction.atomic
    def create(self, validated_data):
        items = validated_data.pop("ingredients")
        cocktail = Cocktail.objects.create(**validated_data)
        self._save_ingredients(cocktail, items)
        return cocktail

    @transaction.atomic
    def update(self, instance, validated_data):
        items = validated_data.pop("ingredients", None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if items is not None:  # PUT lub PATCH z listą: zastępujemy cały przepis
            instance.cocktail_ingredients.all().delete()
            self._save_ingredients(instance, items)
        return instance


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Review
        fields = ["id", "user", "rating", "comment", "created_at"]
        read_only_fields = ["created_at"]
