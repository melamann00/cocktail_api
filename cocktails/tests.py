from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import Cocktail, CocktailIngredient, Ingredient

User = get_user_model()


class BaseTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("anna", "anna@x.pl", "haslo12345")
        self.other = User.objects.create_user("jan", "jan@x.pl", "haslo12345")
        self.admin = User.objects.create_user("root", "root@x.pl", "haslo12345", is_staff=True)
        self.rum = Ingredient.objects.create(name="Rum", is_alcoholic=True)
        self.mint = Ingredient.objects.create(name="Mięta")
        self.soda = Ingredient.objects.create(name="Soda")

    def payload(self, **over):
        data = {
            "name": "Mojito",
            "category": "Long drink",
            "instructions": "Wymieszaj.",
            "ingredients": [
                {"ingredient": self.rum.pk, "measure": "50 ml"},
                {"ingredient": self.mint.pk, "measure": "8 leaf"},
            ],
        }
        data.update(over)
        return data


class AuthTests(BaseTest):
    def test_register_and_login_logout(self):
        r = self.client.post(reverse("register"), {"username": "new", "email": "n@x.pl", "password": "Silnehaslo123"})
        self.assertEqual(r.status_code, 201)
        self.assertNotIn("password", r.data)
        r = self.client.post(reverse("login"), {"username": "new", "password": "Silnehaslo123"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.client.post(reverse("ingredient-list"), {"name": "Gin"}).status_code, 201)
        self.client.post(reverse("logout"))
        self.assertEqual(self.client.post(reverse("ingredient-list"), {"name": "Tonic"}).status_code, 401)

    def test_login_wrong_password(self):
        r = self.client.post(reverse("login"), {"username": "anna", "password": "zle"})
        self.assertEqual(r.status_code, 400)

    def test_basic_auth(self):
        import base64
        cred = base64.b64encode(b"anna:haslo12345").decode()
        r = self.client.post(reverse("ingredient-list"), {"name": "Gin"}, HTTP_AUTHORIZATION=f"Basic {cred}")
        self.assertEqual(r.status_code, 201)

    def test_register_weak_password_rejected(self):
        r = self.client.post(reverse("register"), {"username": "x", "email": "x@x.pl", "password": "12345678"})
        self.assertEqual(r.status_code, 400)

class IngredientTests(BaseTest):
    def test_list_public_and_paginated(self):
        r = self.client.get(reverse("ingredient-list"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["count"], 3)
        r = self.client.get(reverse("ingredient-list"), {"page_size": 2})
        self.assertEqual(len(r.data["results"]), 2)
        self.assertIsNotNone(r.data["next"])

    def test_create_requires_auth(self):
        self.assertEqual(self.client.post(reverse("ingredient-list"), {"name": "Gin"}).status_code, 401)
        self.client.force_authenticate(self.user)
        r = self.client.post(reverse("ingredient-list"), {"name": "Gin", "is_alcoholic": True})
        self.assertEqual(r.status_code, 201)

    def test_duplicate_name_case_insensitive(self):
        self.client.force_authenticate(self.user)
        r = self.client.post(reverse("ingredient-list"), {"name": "rum"})
        self.assertEqual(r.status_code, 400)

    def test_invalid_image_url(self):
        self.client.force_authenticate(self.user)
        r = self.client.post(reverse("ingredient-list"), {"name": "Gin", "image_url": "nie-url"})
        self.assertEqual(r.status_code, 400)

    def test_only_admin_can_edit_and_delete(self):
        url = reverse("ingredient-detail", args=[self.soda.pk])
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.patch(url, {"name": "Woda"}).status_code, 403)
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.patch(url, {"name": "Woda"}).status_code, 200)
        self.assertEqual(self.client.delete(url).status_code, 204)

    def test_delete_used_ingredient_conflict(self):
        self.client.force_authenticate(self.user)
        self.client.post(reverse("cocktail-list"), self.payload(), format="json")
        self.client.force_authenticate(self.admin)
        r = self.client.delete(reverse("ingredient-detail", args=[self.rum.pk]))
        self.assertEqual(r.status_code, 409)

    def test_filter_alcoholic(self):
        r = self.client.get(reverse("ingredient-list"), {"is_alcoholic": "true"})
        self.assertEqual([i["name"] for i in r.data["results"]], ["Rum"])


class CocktailTests(BaseTest):
    def create(self, **over):
        self.client.force_authenticate(self.user)
        return self.client.post(reverse("cocktail-list"), self.payload(**over), format="json")

    def test_create_sets_author_and_recipe(self):
        r = self.create()
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["author"], "anna")
        self.assertTrue(r.data["is_alcoholic"])
        self.assertEqual(len(r.data["recipe"]), 2)
        self.assertEqual(r.data["recipe"][0]["ingredient"]["name"] in ("Rum", "Mięta"), True)

    def test_create_requires_auth(self):
        r = self.client.post(reverse("cocktail-list"), self.payload(), format="json")
        self.assertEqual(r.status_code, 401)

    def test_validation(self):
        bad = [
            self.payload(ingredients=[]),
            self.payload(ingredients=[{"ingredient": 9999, "measure": "5 ml"}]),
            self.payload(ingredients=[{"ingredient": self.rum.pk, "measure": "x" * 101}]),
            self.payload(tags="IBA"),
            self.payload(tags=["ok", ""]),
            self.payload(ingredients=[
                {"ingredient": self.rum.pk, "measure": "5 ml"},
                {"ingredient": self.rum.pk, "measure": "5 ml"},
            ]),
            self.payload(name=""),
            self.payload(category="   "),
        ]
        for data in bad:
            self.client.force_authenticate(self.user)
            r = self.client.post(reverse("cocktail-list"), data, format="json")
            self.assertEqual(r.status_code, 400, data)

    def test_duplicate_name(self):
        self.create()
        self.assertEqual(self.create(name="mojito").status_code, 400)

    def test_only_owner_or_admin_can_modify(self):
        cid = self.create().data["id"]
        url = reverse("cocktail-detail", args=[cid])
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.patch(url, {"category": "X"}, format="json").status_code, 403)
        self.assertEqual(self.client.delete(url).status_code, 403)
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.patch(url, {"category": "Shot"}, format="json").status_code, 200)
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertFalse(Cocktail.objects.filter(pk=cid).exists())

    def test_put_replaces_ingredients(self):
        cid = self.create().data["id"]
        url = reverse("cocktail-detail", args=[cid])
        data = self.payload(ingredients=[{"ingredient": self.soda.pk, "measure": "100 ml"}])
        r = self.client.put(url, data, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual([x["ingredient"]["name"] for x in r.data["recipe"]], ["Soda"])
        self.assertEqual(CocktailIngredient.objects.filter(cocktail_id=cid).count(), 1)

    def test_patch_without_ingredients_keeps_recipe(self):
        cid = self.create().data["id"]
        self.client.patch(reverse("cocktail-detail", args=[cid]), {"name": "Mojito 2"}, format="json")
        self.assertEqual(CocktailIngredient.objects.filter(cocktail_id=cid).count(), 2)

    def test_filtering_and_sorting(self):
        self.create()
        self.create(
            name="Virgin Mojito", category="Bezalkoholowy",
            ingredients=[
                {"ingredient": self.mint.pk, "measure": "8 leaf"},
                {"ingredient": self.soda.pk, "measure": "100 ml"},
            ],
        )
        url = reverse("cocktail-list")
        names = lambda r: [c["name"] for c in r.data["results"]]  # noqa: E731

        self.assertEqual(names(self.client.get(url, {"alcoholic": "false", "ingredient": "mięta"})), ["Virgin Mojito"])
        self.assertEqual(names(self.client.get(url, {"alcoholic": "true"})), ["Mojito"])
        self.assertEqual(len(names(self.client.get(url, {"ingredient": ["mięta", "soda"]}))), 1)
        self.assertEqual(len(names(self.client.get(url, {"ingredient": self.mint.pk}))), 2)
        self.assertEqual(names(self.client.get(url, {"author": "anna", "ordering": "-name"})), ["Virgin Mojito", "Mojito"])
        self.assertEqual(names(self.client.get(url, {"category": "bezalkoholowy"})), ["Virgin Mojito"])
        self.assertEqual(names(self.client.get(url, {"search": "soda"})), ["Virgin Mojito"])

    def test_pagination(self):
        for i in range(12):
            self.create(name=f"Koktajl {i:02d}")
        r = self.client.get(reverse("cocktail-list"))
        self.assertEqual((r.data["count"], len(r.data["results"])), (12, 10))
        r = self.client.get(reverse("cocktail-list"), {"page": 2})
        self.assertEqual(len(r.data["results"]), 2)
        self.assertEqual(self.client.get(reverse("cocktail-list"), {"page": 99}).status_code, 404)

    def test_retrieve_404(self):
        self.assertEqual(self.client.get(reverse("cocktail-detail", args=[999])).status_code, 404)


class ReviewTests(BaseTest):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(self.user)
        self.cid = self.client.post(reverse("cocktail-list"), self.payload(), format="json").data["id"]
        self.url = reverse("cocktail-reviews", args=[self.cid])

    def test_review_flow_and_average(self):
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.post(self.url, {"rating": 4, "comment": "ok"}).status_code, 201)
        self.assertEqual(self.client.post(self.url, {"rating": 5}).status_code, 400)  # druga recenzja
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post(self.url, {"rating": 2}).status_code, 201)
        r = self.client.get(reverse("cocktail-detail", args=[self.cid]))
        self.assertEqual(r.data["average_rating"], 3.0)

    def test_rating_range_and_auth(self):
        self.assertEqual(self.client.post(self.url, {"rating": 6}).status_code, 400)
        self.assertEqual(self.client.post(self.url, {"rating": 0}).status_code, 400)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.post(self.url, {"rating": 5}).status_code, 401)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_review_of_missing_cocktail(self):
        self.assertEqual(self.client.get(reverse("cocktail-reviews", args=[9999])).status_code, 404)
