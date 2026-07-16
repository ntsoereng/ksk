# Khoboko Law Chambers

The public website and content-management foundation for Khoboko Law Chambers, built with Django and Tailwind CSS.

## Features

- Responsive maroon-and-khaki public website
- Email-based custom user model for staff and administrators
- Admin-managed site information: branding, logo, contact details, hero content, About-page content, and social links
- Practice-area and attorney directories with individual profile pages
- Consultation enquiry form and enquiry management in Django admin
- Articles/Insights section with publishing workflow, featured images, branded fallback image, and rich-text authoring
- About, Privacy, and Terms pages appropriate for a legal practice

## Project apps

| App | Purpose |
| --- | --- |
| `apps.accounts` | Custom email-based user model |
| `apps.core` | Site settings, enquiries, and static public pages |
| `apps.practice_areas` | Legal services and practice-area pages |
| `apps.attorneys` | Attorney profiles and practice-area links |
| `apps.articles` | Draft and published legal insights/articles |

## Local setup

1. Create and activate a Python virtual environment, then install dependencies.

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Create `.env` using the following values as a starting point. Never commit this file.

   ```env
   SECRET_KEY=replace-with-a-long-random-value
   DEBUG=true
   ALLOWED_HOSTS=127.0.0.1,localhost
   DB_ENGINE=django.db.backends.mysql
   DB_NAME=khoboko_law
   DB_USER=your_database_user
   DB_PASSWORD=your_database_password
   DB_HOST=127.0.0.1
   DB_PORT=3306
   ```

3. Install frontend dependencies and generate the CSS.

   ```bash
   npm install
   npm run build
   ```

4. Create the schema, an administrator, and start the local server.

   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver
   ```

The administrator signs in using the email address entered during `createsuperuser`; the custom user model does not have a username field.

## Content management

Open `/admin/` after signing in as staff.

- Create one **Site information** record first. It controls the logo, contact details, homepage hero, and About-page copy.
- Add published **Practice areas** and **Attorneys** to populate the public directories.
- Review incoming **Consultation inquiries**.
- Create **Articles** as drafts, add rich content with the editor toolbar, and set the status to Published when ready. Articles without a featured image use the branded default artwork.

Uploaded files are stored in `media/` during development and are intentionally excluded from Git. Arrange persistent media storage for production.

## Frontend commands

```bash
npm run build  # Generate minified static/css/output.css once
npm run watch  # Rebuild CSS while editing templates
```

## Production checklist

- Set `DEBUG=false` and use a unique production `SECRET_KEY`.
- Configure the production hostname in `ALLOWED_HOSTS`.
- Run `python manage.py migrate` and `python manage.py collectstatic`.
- Configure persistent storage for media uploads (logos, attorney images, and article images).
- Use HTTPS and set the relevant Django security settings at the deployment layer.
- Keep `.env`, `media/`, `node_modules/`, and private keys out of version control; `.gitignore` is configured for this.
