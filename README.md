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

The **Image** button in the dashboard’s rich-text editors inserts images into the body of articles, case-study narratives, practice areas and biographies. Choose a JPEG, PNG or WebP file (up to 8 MB and 24 megapixels), or provide an image URL, then add alt text and an optional caption. Uploaded images are stored in `media/content/`, independently of featured images. Save the content after inserting images. Uploads require staff access and permission to add or change the relevant content type.

In **Staff portal → Site settings → Google Maps embed**, paste the iframe code from Google Maps’ **Share → Embed a map**, or its `https://www.google.com/maps/embed…` URL. The contact page shows the responsive map after saving; leave this setting blank to hide it. The separate **Google maps URL** setting supplies the directions link. Run `python manage.py migrate` when deploying the new map setting, followed by the CSS build and `collectstatic` as usual.

## Form protection and website policies

Run migrations before serving the updated application: the `FormRateLimit` table stores atomic request counters shared by all workers using the same database. No additional cache or service is needed. Counters store keyed hashes, expire at the end of each window, and are pruned in bounded batches during subsequent activity. Limits count all attempts, including invalid submissions. A blocked request returns HTTP 429 with a `Retry-After` header; upload requests receive a JSON error. GET requests and staff sign-out remain available.

| Protected action | Default allowance |
| --- | --- |
| Contact enquiries | 5 attempts per network address and 3 per email per 15-minute window |
| Staff and Django admin sign-in, combined | 20 attempts per network address and 10 per account per 15-minute window |
| Staff inline image uploads | 20 attempts per staff account per minute |
| Other staff/admin writes | 90 attempts per staff account per minute |

The `.env.example` lists threshold settings. Forwarded IP headers are ignored unless the connecting peer is in `FORM_TRUSTED_PROXIES`. On a reverse proxy, configure only its exact trusted IPs or CIDRs, and ensure it appends or overwrites `X-Forwarded-For`. The limiter walks that chain from the trusted end. Never configure arbitrary public networks as trusted proxies. Without proxy configuration, requests are safely grouped by the connecting peer, which can mean a shared allowance behind a proxy.

The contact form also has a non-interactive spam-trap field, a 5,000-character message limit, and server-side validation. Existing Django CSRF, staff permissions and image validation remain enabled. Configure request body/connection limits at the reverse proxy as well; application request limits do not replace network-level protection against volumetric traffic. See [Django’s security guidance](https://docs.djangoproject.com/en/6.0/topics/security/).

The default privacy and terms pages now cover initial enquiries, accepting instructions, confidentiality, website use, retention, essential cookies, security counters, external maps and images, privacy requests, and applicable law. Privacy wording was informed by the [Lesotho Data Protection Act published in the Government Gazette](https://www.nic.ls/lsnic/community/policies/Data_Protection_Act_2011_Lesotho.pdf). Dashboard overrides still take precedence: review any existing **Privacy policy** or **Terms of use** values in Site settings if older copy is still displayed. Keep the published policy, revision date, service-provider arrangements and retention practices aligned with the firm’s actual operations.

A dismissible legal-information banner appears on a visitor’s first visit. Dismissal stores only the notice version in browser local storage (`klc-legal-notice-dismissed`). Update `data-notice-version` in `templates/components/legal_notice.html` when a material notice change should be shown again. If storage is blocked, dismissal still works for the current page. The permanent footer notice and policy links remain available.

Uploaded files are stored in the project `media/` directory by default. Set `MEDIA_ROOT` to persistent storage in production. `DJANGO_SERVE_MEDIA=true` lets Django deliver uploads when the hosting platform does not map `/media/`; high-traffic deployments should set it to false after configuring Nginx, Apache, or object storage to serve that directory.

## Search engines and social previews

Every public page has a unique title and description, a canonical URL without tracking parameters, Open Graph and Twitter card metadata, and JSON-LD for the firm, website and page. Detail pages add article, person, service or case-study data and breadcrumbs. Preview images use the content image when available, then the configured social image or logo, then the bundled 1200 × 630 branded card. Update the bundled card if the firm's branding changes.

Set **Public website URL** in staff Site settings to the production HTTPS origin, or set `SITE_URL` in the deployment environment to override it. The canonical URLs, image URLs, `/sitemap.xml` and `/robots.txt` use this same origin. Configure the social image and homepage SEO title/description in Site settings. The sitemap includes public legal pages and only active profiles/services and published, non-future content. Staff and admin routes are disallowed in robots.txt and receive `X-Robots-Tag: noindex, nofollow`; failed responses also receive that header. Authentication still controls access to private content. Crawling restrictions are [distinct from search indexing controls](https://developers.google.com/search/docs/crawling-indexing/robots/intro).

`/.well-known/security.txt` publishes the reporting contact, canonical location, preferred language and a fixed expiry following [RFC 9116](https://www.rfc-editor.org/rfc/rfc9116.html). `/security.txt` permanently redirects there. Set `SECURITY_CONTACT` to a monitored `mailto:` or HTTPS reporting URI; otherwise the firm's configured email is used, falling back to the contact form. Review the reporting contact and renew `SECURITY_EXPIRES` before **1 April 2027**, the default expiry. Serve this endpoint over HTTPS in production. This publishes a reporting channel and does not establish a testing policy or bug bounty.

After deploying, submit `/sitemap.xml` in your search engine webmaster tools and validate representative URLs in the social platforms' preview tools. Run `collectstatic` to publish the bundled sharing image.

## Frontend commands

```bash
npm run build  # Generate minified static/css/output.css once
npm run watch  # Rebuild CSS while editing templates
```

## Production checklist

- Deploy with Python 3.12 or newer and install the pinned dependencies from `requirements.txt`.
- Set `DEBUG=false` and use a unique production `SECRET_KEY`. The security-cookie, HTTPS redirect, and HSTS settings automatically become secure defaults; configure HTTPS at the proxy or web server before deployment.
- Configure the production hostname in `ALLOWED_HOSTS`.
- Run `python manage.py migrate` and `python manage.py collectstatic`.
- Configure persistent storage for media uploads (logos, attorney images, and article images).
- If retaining uploads from the original server layout, set `MEDIA_ROOT=/home/khobokol/media`. Otherwise set it to the absolute persistent directory where the deployed application writes uploads.
- On Apache/cPanel, copy `deployment/media.htaccess` to `MEDIA_ROOT/.htaccess` so uploads can be served but never executed.
- Use HTTPS and set the relevant Django security settings at the deployment layer.
- Keep `.env`, `media/`, `node_modules/`, and private keys out of version control; `.gitignore` is configured for this.

Run the WSGI application with:

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000}
```
