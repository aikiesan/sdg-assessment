# Environment Configuration

**Version:** 1.0.0  
**Last Updated:** 2025-04-25

This file describes the environment variables and configuration required for running the SDG Assessment Toolkit in different environments (development, testing, production).

## Prerequisites
- Python 3.9 or higher
- Access to environment variable configuration (e.g., .env file or system environment)

## Required Environment Variables

| Variable Name      | Description                                 | Example Value              |
|--------------------|---------------------------------------------|----------------------------|
| FLASK_CONFIG       | Flask config profile (dev/test/prod)         | development                |
| SECRET_KEY         | Flask secret key for sessions                | supersecretkey             |
| DATABASE_URL       | Database connection string                   | sqlite:///sdg_assessment.db|
| MAIL_SERVER        | SMTP server for outgoing email (optional)    | smtp.example.com           |
| MAIL_PORT          | SMTP port                                    | 587                        |
| MAIL_USERNAME      | Email username                               | user@example.com           |
| MAIL_PASSWORD      | Email password                               | password                   |
| MAIL_USE_TLS       | Enable TLS (true/false)                      | true                       |

> **Note:** If there are any additional or deprecated environment variables, please let me know so I can update this list.

## Sample .env File
```env
FLASK_CONFIG=development
SECRET_KEY=your_secret_key
DATABASE_URL=sqlite:///sdg_assessment.db
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USERNAME=user@example.com
MAIL_PASSWORD=password
MAIL_USE_TLS=true
```

## Configuration Profiles

- **Development:**
  - Use SQLite and enable debug mode.
  - Example: `FLASK_CONFIG=development`
- **Testing:**
  - Use a separate test database, enable testing mode.
  - Example: `FLASK_CONFIG=testing`
- **Production:**
  - Use a production-ready database and strong secret keys.
  - Example: `FLASK_CONFIG=production`

See `config.py` for more details on configuration options.

## Troubleshooting
- **App fails to start:** Check that all required environment variables are set and spelled correctly.
- **Database connection errors:** Verify your `DATABASE_URL` and ensure the database server is running.
- **Email not sending:** Double-check your mail server settings and credentials.
- **Configuration changes not taking effect:** Restart the application after updating environment variables.

For environment/configuration support, contact Lucas Nakamura at [lucassnakamura@gmail.com](mailto:lucassnakamura@gmail.com).

---
**Maintained by Lucas Nakamura**
