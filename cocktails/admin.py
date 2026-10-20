from django.contrib import admin

from .models import Cocktail, CocktailIngredient, Ingredient, Review


class CocktailIngredientInline(admin.TabularInline):
    model = CocktailIngredient
    extra = 1


@admin.register(Cocktail)
class CocktailAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "author"]
    inlines = [CocktailIngredientInline]


admin.site.register(Ingredient)
admin.site.register(Review)
