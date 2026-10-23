# Cocktail API

A simple REST API for browsing and managing cocktail recipes, built with Django.

## Example endpoints

| Method | Endpoint             | Description          |
|--------|----------------------|----------------------|
| GET    | `api/cocktails/`        | List all cocktails   |
| GET    | `api/cocktails/<id>/`   | Get one cocktail     |
| POST   | `/cocktails/`        | Create a cocktail    |
| PUT    | `/cocktails/<id>/`   | Update a cocktail    |
| DELETE | `/cocktails/<id>/`   | Delete a cocktail    |


## Example response

```json
{
  "id": 1,
  "name": "Mojito",
  "ingredients": ["white rum", "mint", "lime", "sugar", "soda water"]
}
```

## Testing

Import the collection from the `.postman` folder into Postman and send requests to the running server.

## Author

[melamann00](https://github.com/melamann00)