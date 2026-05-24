# Module Decomposition

## Codebase structure

- `app.py` - Main backend application, routes, auth, prediction, mail, session logic
- `templates/` - Jinja HTML templates
- `static/` - Frontend assets (CSS/JS)
- `model/` - Trained TensorFlow model file
- `uploads/` - Runtime image uploads (ignored in git)
- `docs/` - Technical documentation

## Backend decomposition (`app.py`)

## A) Configuration and constants

- Secret key and session timeout configuration
- Upload folder and file constraints
- Model loading and class label metadata
- MongoDB URI and collection initialization

## B) Utility functions

- Input normalization and validation helpers
- File validation helpers
- Database access wrappers (`get_user`, `create_user`, etc.)
- Mail utility (`send_mail`)
- Password reset token storage helpers

## C) Session management

- `before_request` hook tracks inactivity
- Session cleanup on timeout
- Optional keepalive support via `/session/ping`

## D) Route groups

1. **Public pages**
   - `/` home
2. **Auth**
   - `/register`
   - `/login`
   - `/logout`
3. **Password recovery**
   - `/forgot-password`
   - `/reset-password/<token>`
4. **Dashboard and inference**
   - `/dashboard`
   - `/predict`
5. **Session utility**
   - `/session/ping`

## Frontend decomposition

## A) Templates

- `home.html` - Landing page and marketing section
- `login.html` - Login form and flash messages
- `register.html` - Registration form with validation feedback
- `forgot_password.html` - Reset request form
- `reset_password.html` - New password form
- `index.html` - Dashboard for upload and prediction

## B) JavaScript

- `static/script.js`
  - Image preview
  - API call to `/predict`
  - Response rendering (prediction details, top predictions, warnings)
- `static/session-timeout.js`
  - User activity tracking
  - Inactivity logout timer
  - Session keepalive ping

## C) CSS

- `static/style.css`
  - Global theme and typography
  - Shared header/footer styles across all pages
  - Auth page styling
  - Dashboard cards, prediction panel, and history grid
