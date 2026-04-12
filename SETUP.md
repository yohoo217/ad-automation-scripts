# Setup Guide

## 1. Create Local Configuration

```bash
cp .env.example .env
```

At minimum, configure the following fields:

```bash
SECRET_KEY=change-me
ALLOWED_EMAILS=portfolio-owner@example.com,reviewer@example.edu

MONGO_CONNECTION_STRING=mongodb://localhost:27017/automation_demo
MONGO_DATABASE=automation_demo

PLATFORM_EMAIL=automation.user@example.com
PLATFORM_PASSWORD=change-me
PLATFORM_COOKIE=
PREVIEW_COOKIE=
PLATFORM_ORG_LABEL=Example Organization
```

## 2. Install Dependencies

```bash
pip install -r requirements.txt
playwright install
```

## 3. Start the Application

```bash
python run.py
```

The application starts by default at `http://localhost:5002`.

## 4. Configuration Recommendations for Portfolio Use

- Do not enter real customer data, actual cookies, or production account credentials
- Retain only test data and anonymized configuration sufficient to demonstrate the workflow
- If demonstrating screenshot or report pages, prepare your own test data source

## Security Notes

- `.env` should not be committed to version control
- Real cookies, API keys, and service account files should not be stored in the repository
- When presenting publicly, use dedicated demo accounts and a demo database

## Troubleshooting

### MongoDB Connection Failure

1. Verify that MongoDB is running
2. Check the connection string and database name in `.env`
3. If you only want to showcase the UI, you can skip pages that require a database

### Playwright Installation Fails

```bash
playwright install --with-deps
```

### Screenshots or Reports Not Loading

- This public version does not include any production environment cookies
- To demonstrate these pages, add test environment cookies to your `.env` file

## Development Notes

- `app/routes/` contains the main workflow routes
- `templates/` contains pages for various content formats
- `app/services/url_builder.py` and `app/routes/screenshot.py` demonstrate the engineering design of the screenshot workflow
- `app/routes/main.py` demonstrates data query and report integration logic
