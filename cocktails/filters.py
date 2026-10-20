import django_filters as df
from django.db.models import Q

from .models import Cocktail, Ingredient


class IngredientFilter(df.FilterSet):
    name = df.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Ingredient
        fields = ["name", "is_alcoholic"]


class CocktailFilter(df.FilterSet):
    name = df.CharFilter(lookup_expr="icontains")
    category = df.CharFilter(lookup_expr="iexact")
    author = df.CharFilter(field_name="author__username", lookup_expr="iexact")
    # ?alcoholic=false -> koktajle bez żadnego alkoholowego składnika
    alcoholic = df.BooleanFilter(method="filter_alcoholic")
    # ?ingredient=mięta lub ?ingredient=3 (po nazwie lub id), można podać wiele razy -> wszystkie muszą wystąpić
    ingredient = df.CharFilter(method="filter_ingredient")

    class Meta:
        model = Cocktail
        fields = ["name", "category", "author", "alcoholic", "ingredient"]

    def filter_alcoholic(self, queryset, name, value):
        has_alcohol = Q(ingredients__is_alcoholic=True)
        ids = Cocktail.objects.filter(has_alcohol).values("pk")
        return queryset.filter(pk__in=ids) if value else queryset.exclude(pk__in=ids)

    def filter_ingredient(self, queryset, name, value):
        for term in self.request.query_params.getlist("ingredient"):
            cond = Q(ingredients__name__icontains=term)
            if term.isdigit():
                cond |= Q(ingredients__pk=int(term))
            queryset = queryset.filter(pk__in=Cocktail.objects.filter(cond).values("pk"))
        return queryset
