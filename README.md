# City Prime Bank — Django Site

This is the Django version of the City Prime Bank demo site (previously a static HTML/CSS/JS site).
All pages, styling, and the client-side JS (balances, transactions, toasts, sidebar) are unchanged —
they're now served through Django views/templates instead of static HTML files.

## Project layout

```
bankdjango/
├── manage.py
├── requirements.txt
├── bankproject/          # Django project settings
│   ├── settings.py
│   ├── urls.py           # includes bank.urls
│   └── ...
└── bank/                 # Django app
    ├── views.py           # one TemplateView per page
    ├── urls.py            # named routes (bank:index, bank:dashboard, ...)
    ├── templates/bank/    # all .html pages (converted to Django templates)
    └── static/bank/assets/ # style.css + app.js
```

## Routes

| URL              | Template          | Name                  |
|-------------------|-------------------|------------------------|
| `/`               | index.html        | `bank:index`           |
| `/login/`         | login.html        | `bank:login`           |
| `/register/`      | register.html     | `bank:register`        |
| `/dashboard/`     | dashboard.html    | `bank:dashboard`       |
| `/accounts/`      | accounts.html     | `bank:accounts`        |
| `/transfer/`      | transfer.html     | `bank:transfer`        |
| `/deposit/`       | deposit.html      | `bank:deposit`         |
| `/help-center/`   | help-center.html  | `bank:help_center`     |
| `/settings/`      | settings.html     | `bank:settings_page`   |

All internal links in the templates use `{% url 'bank:...' %}` instead of hardcoded `.html` paths,
including anchored links like `{% url 'bank:accounts' %}#cards`.

## Running locally

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py runserver
```

Then open http://127.0.0.1:8000/ in your browser.

## Notes

- The site currently has no real backend logic (no database-backed accounts, auth, or transactions) —
  balances/transactions are still simulated client-side in `assets/app.js`, exactly like the static
  version. Login/Register forms don't authenticate against a database yet.
- `django.contrib.auth` is already installed and ready if you want to wire up real user accounts later.
- Static files are served via Django's `staticfiles` app in development. For production, run
  `python manage.py collectstatic` and serve `/static/` via your web server or a CDN.
