# Architecture Documentation

## Overview

SmartAahar AI is a Flask web application that provides:

- User registration and login
- Password reset via email
- Image upload and food prediction using a TensorFlow model
- Prediction history storage in MongoDB

The app follows a server-rendered architecture with Jinja templates and static JS/CSS.

## High-level components

1. **Presentation Layer**
   - HTML templates in `templates/`
   - CSS and JS in `static/`
2. **Application Layer**
   - Flask routes and business logic in `app.py`
3. **AI Inference Layer**
   - TensorFlow model loaded from `model/gujarati_food_model.keras`
4. **Data Layer**
   - MongoDB (`food_ai` database) with `users` and `predictions` collections
   - In-memory fallback when MongoDB is unavailable
5. **External Services**
   - SMTP mail server for welcome and reset emails

## Request flow

## 1) Authentication flow

- User opens `/register` or `/login`
- Server validates input and hashes passwords via bcrypt
- Session cookie stores authenticated user state
- Session timeout enforced by inactivity checks

## 2) Prediction flow

- Authenticated user uploads image from `/dashboard`
- Frontend sends `POST /predict` with multipart image
- Backend:
  - validates file extension and size
  - preprocesses image to `(224, 224)` and rescales to `[0, 1]`
  - runs model inference
  - maps class index to label and food details
  - applies confidence threshold for non-food rejection
  - stores prediction in DB
- API returns prediction, confidence, suggestions, top predictions

## 3) Password reset flow

- User submits email at `/forgot-password`
- Backend creates secure time-limited token
- Reset link is sent by SMTP
- User submits new password at `/reset-password/<token>`

## Security and reliability notes

- Passwords are hashed (bcrypt), never stored plain text
- Upload restrictions:
  - allowed extensions: png/jpg/jpeg/webp
  - max size: 5MB
- Session expiration:
  - server-side inactivity timeout
  - client-side keepalive + idle logout
- MongoDB connection fallback:
  - app stays usable in local memory mode if DB is unavailable
