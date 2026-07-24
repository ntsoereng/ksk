# Khoboko Law Chambers

The public website and content-management foundation for Khoboko Law Chambers, built with Django and Tailwind CSS.

## Features

- Responsive maroon-and-khaki public website
- Email-based custom user model for staff and administrators
- Admin-managed site information: branding, logo, contact details, hero content, About-page content, and social links
- Practice-area and people directories with separate legal-professional and staff sections
- Consultation enquiry form and enquiry management in Django admin
- Branded, permission-aware staff dashboard for posts, practice areas, people, case studies, site settings, and contact enquiries
- Draft/published case-study workflow with confidentiality guidance
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
   SECURE_SSL_REDIRECT=false
   SESSION_COOKIE_SECURE=false
   CSRF_COOKIE_SECURE=false
   SECURE_HSTS_SECONDS=0
   SECURE_HSTS_PRELOAD=false
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

Staff can also use the branded portal at `/staff/`; a discreet sign-in link appears in the website footer. This is the primary content workspace, with front-end list, create, edit and delete screens for posts, practice areas, case studies and people, plus site settings and contact-message review. Rich-text fields use an allow-list-sanitised editor. Dashboard sections follow each account's Django permissions, so content editors do not need unrestricted administrator access. Django admin remains available as a fallback.

- Create one **Site information** record first. It controls branding, contact details, homepage sections, people-page introductions, About content, and website notices. Blank optional fields use built-in fallback copy.
- Add published **Practice areas** and people profiles to populate the public directories. Classify every profile as a **Legal professional** or **Professional & support staff**, then use display order to set hierarchy inside that group.
- Review incoming **Consultation inquiries**.
- Create **Articles** as drafts, add rich content with the editor toolbar, and set the status to Published when ready. Articles without a featured image use the branded default artwork.

Uploaded files are stored in the project `media/` directory and served by Django while `DEBUG=true`. Set `MEDIA_ROOT` to persistent storage in production; the path is no longer tied to a particular server account.

## Frontend commands

```bash
npm run build  # Generate minified static/css/output.css once
npm run watch  # Rebuild CSS while editing templates
```

## Production checklist

- Set `DEBUG=false` and use a unique production `SECRET_KEY`. The security-cookie, HTTPS redirect, and HSTS settings automatically become secure defaults; configure HTTPS at the proxy or web server before deployment.
- Configure the production hostname in `ALLOWED_HOSTS`.
- Run `python manage.py migrate` and `python manage.py collectstatic`.
- Configure persistent storage for media uploads (logos, attorney images, and article images).
- Use HTTPS and set the relevant Django security settings at the deployment layer.
- Keep `.env`, `media/`, `node_modules/`, and private keys out of version control; `.gitignore` is configured for this.
