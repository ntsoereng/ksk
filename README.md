# Khoboko Law Chambers

A Django website foundation for Khoboko Law Chambers.

## Included

- Email-first custom user model in `apps.accounts` (set before the first migration)
- Manageable practice areas and attorney profiles, with public directory pages
- Homepage and consultation inquiry form, with inquiries available in Django admin
- Tailwind CSS build scripts for the public site

## Local setup

1. Create and activate a Python virtual environment, then install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Set the required database and security values in `.env`:

   ```env
   SECRET_KEY=change-me
   DEBUG=true
   DB_ENGINE=django.db.backends.mysql
   DB_NAME=khoboko_law
   DB_USER=your_database_user
   DB_PASSWORD=your_database_password
   DB_HOST=127.0.0.1
   DB_PORT=3306
   ```

3. Install frontend packages and build CSS:

   ```bash
   npm install
   npm run build
   ```

4. Create the database tables and an administrator:

   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver
   ```

Use `/admin/` to add practice areas, attorney profiles, and review consultation inquiries. Do not deploy with `DEBUG=true`.
