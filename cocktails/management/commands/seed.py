from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from cocktails.models import Cocktail, CocktailIngredient, Ingredient

INGREDIENTS = {
    "Biały rum": ("Lekki rum do koktajli.", True),
    "Wódka": ("Neutralny destylat zbożowy.", True),
    "Sok z limonki": ("Świeżo wyciskany.", False),
    "Mięta": ("Świeże listki mięty.", False),
    "Cukier": ("Biały cukier lub syrop cukrowy.", False),
    "Woda gazowana": ("Do dopełnienia.", False),
    "Sok pomarańczowy": ("Najlepiej świeży.", False),
}

COCKTAILS = [
    ("Mojito", "Long drink", "Rozgnieć miętę z cukrem i limonką, dodaj rum, lód i dopełnij wodą gazowaną.",
     [("Biały rum", 50, "ml"), ("Sok z limonki", 25, "ml"), ("Mięta", 8, "leaf"),
      ("Cukier", 2, "tsp"), ("Woda gazowana", 60, "ml")]),
    ("Virgin Mojito", "Bezalkoholowy", "Jak Mojito, ale bez rumu - więcej wody gazowanej.",
     [("Sok z limonki", 25, "ml"), ("Mięta", 8, "leaf"), ("Cukier", 2, "tsp"),
      ("Woda gazowana", 120, "ml")]),
    ("Screwdriver", "Long drink", "Wlej wódkę do szklanki z lodem i dopełnij sokiem pomarańczowym.",
     [("Wódka", 50, "ml"), ("Sok pomarańczowy", 100, "ml")]),
]


class Command(BaseCommand):
    help = "Wypełnia bazę przykładowymi danymi (składniki, koktajle, użytkownicy)."

    def handle(self, *args, **options):
        User = get_user_model()
        admin, _ = User.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@example.com", "is_staff": True, "is_superuser": True},
        )
        admin.set_password("admin12345")
        admin.save()
        user, _ = User.objects.get_or_create(username="user", defaults={"email": "user@example.com"})
        user.set_password("user12345")
        user.save()

        ing = {}
        for name, (desc, alc) in INGREDIENTS.items():
            ing[name], _ = Ingredient.objects.get_or_create(
                name=name, defaults={"description": desc, "is_alcoholic": alc}
            )
        for name, category, instructions, items in COCKTAILS:
            cocktail, created = Cocktail.objects.get_or_create(
                name=name,
                defaults={"category": category, "instructions": instructions, "author": user},
            )
            if created:
                CocktailIngredient.objects.bulk_create(
                    CocktailIngredient(cocktail=cocktail, ingredient=ing[i], quantity=q, unit=u)
                    for i, q, u in items
                )
        self.stdout.write(self.style.SUCCESS("Gotowe. Konta: admin/admin12345, user/user12345"))
