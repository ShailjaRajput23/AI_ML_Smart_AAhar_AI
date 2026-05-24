# SmartAahar AI

Flask web app for Gujarati food image prediction with authentication, MongoDB persistence, and password reset via email.

## Features

- User registration and login
- Registration form validation
- Welcome email on registration
- Forgot password + reset link flow
- Protected prediction API (requires login)
- Image upload + TensorFlow model inference
- Prediction history on dashboard
- Local MongoDB support by default

## Local setup

1. Create and activate environment:

```bash
python3.11 -m venv .venv311
source .venv311/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure env vars:

```bash
cp .env.example .env
```

4. Start local MongoDB:

```bash
brew tap mongodb/brew
brew install mongodb-community@7.0
brew services start mongodb-community@7.0
```

5. Export env variables (or use your shell profile):

```bash
export SECRET_KEY="replace_me"
export MONGO_URI="mongodb://localhost:27017/"
export MAIL_SERVER="smtp.gmail.com"
export MAIL_PORT="587"
export MAIL_USERNAME="your_email@gmail.com"
export MAIL_PASSWORD="your_app_password"
export MAIL_FROM="SmartAahar AI <your_email@gmail.com>"
export MAIL_USE_TLS="true"
```

6. Run app:

```bash
flask --app app run --debug --port 5051
```

Open: http://127.0.0.1:5051

## Deploy on Render + MongoDB Atlas (Free)

1. Create a free MongoDB Atlas cluster (M0), database user, and network access rule.
2. Copy your Atlas connection string and replace password in URI.
3. Push this project to GitHub (steps below).
4. In Render, create a new Web Service from your GitHub repo.
5. Render can auto-detect `render.yaml`, or set manually:
   - Build command: `pip install -r requirements-prod.txt`
   - Start command: `gunicorn app:app`
6. Add environment variables in Render dashboard:
   - `MONGO_URI` = your Atlas URI
   - `SECRET_KEY` = strong random value
   - `SESSION_TIMEOUT_MINUTES` = `10`
   - `MIN_FOOD_CONFIDENCE` = `0.70`
   - Mail variables (`MAIL_*`) if you want email features

## Push project to GitHub

> `uploads/` is already ignored in `.gitignore`, so uploaded images will not be committed.

```bash
cd "/Users/janmaijaysingh/Downloads/AIML project"
git init
git add .
git commit -m "Initial SmartAahar AI app"
git branch -M main
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main
```

Example repo URL:

- HTTPS: `https://github.com/<username>/<repo>.git`
- SSH: `git@github.com:<username>/<repo>.git`
