# Setup and Deployment Steps

## Local setup (macOS)

1. Create virtual environment:

```bash
python3.11 -m venv .venv311
source .venv311/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment:

```bash
cp .env.example .env
```

Set at least:

- `SECRET_KEY`
- `MONGO_URI`

Optional:

- `SESSION_TIMEOUT_MINUTES`
- `MIN_FOOD_CONFIDENCE`
- `MAIL_*` values for email features

4. Run app:

```bash
flask --app app run --debug --port 5051
```

## MongoDB local (optional)

```bash
brew tap mongodb/brew
brew install mongodb-community@7.0
brew services start mongodb-community@7.0
```

## GitHub push

```bash
git add .
git commit -m "Update project documentation"
git push
```

## Render cloud deployment

The project includes:

- `render.yaml`
- `Procfile`
- `requirements-prod.txt`

### Render settings

- Build command: `pip install -r requirements-prod.txt`
- Start command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 180`

### Required environment variables on Render

- `SECRET_KEY`
- `MONGO_URI`
- `SESSION_TIMEOUT_MINUTES`
- `MIN_FOOD_CONFIDENCE`

### Optional environment variables on Render

- `MAIL_SERVER`
- `MAIL_PORT`
- `MAIL_USERNAME`
- `MAIL_PASSWORD`
- `MAIL_FROM`
- `MAIL_USE_TLS`

## MongoDB Atlas setup summary

1. Create M0 cluster
2. Create DB user (password auth)
3. Add network access IP (`0.0.0.0/0` for demo/dev)
4. Copy Atlas URI and set in `MONGO_URI`
