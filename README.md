# Workflow Automation Dashboard

This repository contains a sanitized version of a workflow automation project built with Flask and Playwright. The application turns a repetitive multi-step browser workflow into a web-based dashboard with structured forms, batch operations, reporting utilities, and screenshot generation.

The public version keeps the architecture and implementation patterns while removing organization-specific labels, private URLs, credentials, cookies, and machine-specific paths.

## Features

- Multi-page Flask application for launching automation tasks from a browser UI
- Reusable Jinja templates for different content formats and workflow variants
- Browser automation with Playwright for form submission and multi-step task execution
- Single-item and batch processing flows
- Upload handling, validation, error reporting, and logging
- Reporting and screenshot utilities backed by database lookups and generated preview URLs

## Tech Stack

- Python
- Flask
- Playwright
- Jinja2
- MongoDB
- HTML, CSS, JavaScript

## Project Goals

- Replace repetitive manual browser work with reproducible automation flows
- Provide a UI layer on top of automation scripts so the workflow is easier to operate
- Keep related routes, templates, utilities, and automation logic organized by responsibility
- Make the project safer to share by moving sensitive configuration into environment variables

## Quick Start

1. Install dependencies:

```bash
pip install -r requirements.txt
playwright install
```

2. Create a local environment file:

```bash
cp .env.example .env
```

3. Start the application:

```bash
python run.py
```

4. Open `http://localhost:5002`

For local configuration details, see `SETUP.md`.

## Repository Layout

```text
.
├── app/
│   ├── models/       # Database access and query helpers
│   ├── routes/       # Flask routes and APIs
│   ├── services/     # Supporting business logic
│   ├── utils/        # Shared utilities and auth helpers
│   └── static/       # Static assets
├── templates/        # Jinja templates
├── ad_scheduler/     # Additional batch/scheduling flow examples
├── config.py         # Environment-driven configuration
├── SETUP.md          # Local setup notes
└── run.py            # Application entry point
```

## Notes

- This repository does not include working production credentials.
- Any external integrations should be configured through your own `.env` values.
- The codebase is intended to preserve the engineering approach while avoiding disclosure of private operational details.
