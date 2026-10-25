# Cocktail API

A simple REST API for browsing and managing cocktail recipes, built with Django and Django REST Framework.

## Authentication

The API uses session authentication. Log in via `POST /api/login/` and the server sets a session cookie. For `POST`, `PUT`, `PATCH` and `DELETE` requests, send the `csrftoken` cookie value in the `X-CSRFToken` header.

| Method | Endpoint          | Description                                  | Auth |
|--------|-------------------|----------------------------------------------|------|
| POST   | `/api/register/`  | Create an account (`username`, `email`, `password`) | No |
| POST   | `/api/login/`     | Log in (`username`, `password`)              | No   |
| POST   | `/api/logout/`    | Log out                                      | Yes  |

## Cocktails

| Method | Endpoint                | Description                              | Auth             |
|--------|-------------------------|------------------------------------------|------------------|
| GET    | `/api/cocktails/`       | List all cocktails (supports filtering, search, ordering) | No |
| GET    | `/api/cocktails/<id>/`  | Get one cocktail                         | No               |
| POST   | `/api/cocktails/`       | Create a cocktail                        | Yes              |
| PUT    | `/api/cocktails/<id>/`  | Update a cocktail                        | Author or admin  |
| PATCH  | `/api/cocktails/<id>/`  | Partially update a cocktail              | Author or admin  |
| DELETE | `/api/cocktails/<id>/`  | Delete a cocktail                        | Author or admin  |

## Ingredients

| Method | Endpoint                  | Description              | Auth  |
|--------|---------------------------|--------------------------|-------|
| GET    | `/api/ingredients/`       | List all ingredients     | No    |
| GET    | `/api/ingredients/<id>/`  | Get one ingredient       | No    |
| POST   | `/api/ingredients/`       | Create an ingredient     | Yes   |
| PUT    | `/api/ingredients/<id>/`  | Update an ingredient     | Admin |
| PATCH  | `/api/ingredients/<id>/`  | Partially update         | Admin |
| DELETE | `/api/ingredients/<id>/`  | Delete an ingredient     | Admin |

## Reviews

| Method | Endpoint                                    | Description                    | Auth            |
|--------|---------------------------------------------|--------------------------------|-----------------|
| GET    | `/api/cocktails/<id>/reviews/`              | List reviews of a cocktail     | No              |
| POST   | `/api/cocktails/<id>/reviews/`              | Add a review (one per user)    | Yes             |
| GET    | `/api/cocktails/<id>/reviews/<review_id>/`  | Get one review                 | No              |
| PUT    | `/api/cocktails/<id>/reviews/<review_id>/`  | Update a review                | Author or admin |
| PATCH  | `/api/cocktails/<id>/reviews/<review_id>/`  | Partially update a review      | Author or admin |
| DELETE | `/api/cocktails/<id>/reviews/<review_id>/`  | Delete a review                | Author or admin |

## Creating a cocktail

`POST /api/cocktails/` (logged in). Ingredients are referenced by id, so create them first via `POST /api/ingredients/`.

```json
{
  "name": "Mojito",
  "category": "Highball",
  "glass": "Highball glass",
  "tags": ["refreshing", "summer"],
  "instructions": "Muddle mint with lime and sugar, add rum and ice, top with soda water.",
  "ingredients": [
    {"ingredient": 1, "measure": "50 ml"},
    {"ingredient": 2, "measure": "8 leaves"}
  ]
}
```

## Example response

```json
{
  "id": 1,
  "name": "Mojito",
  "category": "Highball",
  "recipe": [
    {"ingredient": {"id": 1, "name": "White rum", "is_alcoholic": true}, "measure": "50 ml"}
  ],
  "is_alcoholic": true,
  "average_rating": 4.5,
  "author": "melman"
}
```

## Testing

Import the collection from the `.postman` folder into Postman and send requests to the running server.

## Author

[melamann00](https://github.com/melamann00)