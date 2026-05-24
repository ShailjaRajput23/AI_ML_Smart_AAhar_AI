# Database Documentation

## Database technology

- MongoDB (Atlas cloud or local instance)
- Database name: `food_ai`

## Collections

## 1) `users`

Stores authentication and account metadata.

### Typical document

```json
{
  "_id": "ObjectId(...)",
  "username": "student1",
  "email": "student@example.com",
  "password": "$2b$12$hashed_password_value",
  "created_at": "2026-05-24T16:00:00Z",
  "reset_token": "optional_token",
  "reset_expires_at": "optional_datetime"
}
```

### Notes

- `email` is unique (unique index)
- `password` uses bcrypt hash
- reset fields are temporary and removed after successful reset

## 2) `predictions`

Stores each prediction performed by users.

### Typical document

```json
{
  "_id": "ObjectId(...)",
  "user": "student@example.com",
  "image": "4b8f....webp",
  "prediction": "Thepla",
  "prediction_key": "thepla",
  "confidence": 0.91,
  "is_food": true,
  "created_at": "2026-05-24T16:05:00Z"
}
```

### Notes

- Indexed by `user` and `created_at` for recent history retrieval
- `is_food` supports threshold-based rejection handling

## Indexes

- `users.email` unique index
- `predictions.user + predictions.created_at` compound index

## Connection configuration

Configured via environment variable:

- `MONGO_URI`

Examples:

- Local: `mongodb://localhost:27017/`
- Atlas: `mongodb+srv://<user>:<password>@<cluster>/food_ai?...`

## Fallback behavior

If MongoDB is unavailable during app startup:

- App falls back to in-memory storage
- Data is not persistent across restarts
- Useful for development/testing only
