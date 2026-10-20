import json
from pathlib import Path

from django.conf import settings
from django.core.management import color
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from cocktails.models import Cocktail, CocktailIngredient, Ingredient


class Command(BaseCommand):
    help = "Importuje koktajle i składniki z pliku JSON (domyślnie data/cocktail_dataset.json)."

    def add_arguments(self, parser):
        parser.add_argument(
            "path", nargs="?", default=str(Path(settings.BASE_DIR) / "data" / "cocktail_dataset.json")
        )

    @transaction.atomic
    def handle(self, *args, **options):
        path = Path(options["path"])
        if not path.exists():
            raise CommandError(f"Nie znaleziono pliku: {path}")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise CommandError(f"Niepoprawny JSON: {e}")
        if not isinstance(data, list):
            raise CommandError("Plik powinien zawierać listę koktajli.")

        n_ing = n_cocktails = 0
        seen_ingredients = set()
        for item in data:
            for ing in item.get("ingredients") or []:
                if ing["id"] in seen_ingredients:
                    continue
                seen_ingredients.add(ing["id"])
                Ingredient.objects.update_or_create(
                    id=ing["id"],
                    defaults={
                        "name": ing["name"].strip(),
                        "description": ing.get("description") or "",
                        "type": ing.get("type") or "",
                        "percentage": ing.get("percentage"),
                        "is_alcoholic": bool(ing.get("alcohol")),
                        "image_url": ing.get("imageUrl") or "",
                    },
                )
                n_ing += 1

            cocktail, _ = Cocktail.objects.update_or_create(
                id=item["id"],
                defaults={
                    "name": item["name"].strip(),
                    "category": item.get("category") or "",
                    "glass": item.get("glass") or "",
                    "tags": item.get("tags") or [],
                    "instructions": item.get("instructions") or "",
                    "image_url": item.get("imageUrl") or "",
                },
            )
            # przepis zastępujemy w całości, więc import można uruchamiać wielokrotnie
            cocktail.cocktail_ingredients.all().delete()
            CocktailIngredient.objects.bulk_create(
                CocktailIngredient(
                    cocktail=cocktail,
                    ingredient_id=ing["id"],
                    measure=(ing.get("measure") or "").strip(),
                )
                for ing in item.get("ingredients") or []
            )
            n_cocktails += 1

        # Zachowaliśmy id z pliku, więc w PostgreSQL trzeba przesunąć liczniki id.
        if connection.vendor == "postgresql":
            sql = connection.ops.sequence_reset_sql(color.no_style(), [Cocktail, Ingredient])
            with connection.cursor() as cursor:
                for statement in sql:
                    cursor.execute(statement)

        self.stdout.write(
            self.style.SUCCESS(f"Zaimportowano {n_cocktails} koktajli i {n_ing} składników.")
        )
