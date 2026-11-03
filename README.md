# ECE444 PRA6 — Flaskr TDD and Web App Deployment

A Flask blog with login/logout, adding and deleting entries, and case-insensitive title/body search. Uses Bootstrap, JavaScript, Flask-SQLAlchemy, SQLite locally, and PostgreSQL on Render.

Adapted from the [course tutorial](https://github.com/shuruizUofT/flaskr-tdd/blob/main/README.md) at commit `9ba4e4a8143248b9b8c59242b6cdd20abb75d185`, itself adapted from [Michael Herman's Flaskr tutorial](https://github.com/mjhea0/flaskr-tdd). The original MIT license is retained. AI assistance was used for implementation and verification; review the code and explain it in your own words.

## Live application

**[Open the deployed Flaskr app](https://ece444-pra6-6t69.onrender.com/)** · [Health check](https://ece444-pra6-6t69.onrender.com/health)

Deployed on Render with Gunicorn and a separate Render PostgreSQL database (`ece444-pra6-db`). The web service and database use the Free plan in Ohio (US East).

- **Verified on November 2, 2026:** Render reports **Deploy succeeded | Live**, `/health` returns HTTP 200, and the deployed app supports a logged-in session and search results for an existing post.
- **App login:** username `admin` (unless `ADMIN_USERNAME` was changed), with the password configured as `ADMIN_PASSWORD` in Render. These credentials are separate from the Render account login. Passwords and database connection URLs are not stored in this repository.
- **Remaining live checks:** verify adding and deleting a disposable post, blocking deletion after logout, and preserving a post across a service restart or redeploy. Automated/local checks for these behaviors are described below.

The Free PostgreSQL instance currently shows an expiration date of **December 2, 2026**. Free web services can take longer to respond after inactivity; open the app before the TA demonstration.

## Run locally

Requires Python 3.12. From this repository's root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python create_db.py
python -m flask --app project.app run --port 5001
```

Open http://127.0.0.1:5001. The local default username and password are both `admin`. Override them with `ADMIN_USERNAME` and `ADMIN_PASSWORD` in your shell. SQLite is stored in `instance/flaskr.db`; it is excluded from Git. `create_db.py` creates missing tables and preserves existing posts.

## Verify

```sh
python -m pytest -v
python -m flake8 .
python -m black --check .
```

Verified locally: **29 tests passed**, Flake8 passed, and Black passed. GitHub Actions runs these checks on pushes and pull requests. [Verified passing CI run](https://github.com/YilingZha233/ece444-pra6/actions/runs/41564643663). Most tests exercise Flask routes and a real temporary SQLite database; they are integration tests rather than isolated unit tests. PostgreSQL URL selection is tested without opening a remote connection. Live deployment status and the remaining live verification checks are listed above; the automated suite does not connect to the Render database.

## What is included

| Tutorial activity | Implementation / evidence |
| --- | --- |
| First test and database | `tests/app_test.py`; independent temporary databases |
| Templates and views | `project/views.py`, `project/templates/` |
| Style and Bootstrap | Bootstrap 5.3.2 and `project/static/style.css` |
| JavaScript deletion | `project/static/main.js`; explicit Delete buttons |
| SQLAlchemy | `project/models.py`, `project/extensions.py`, `create_db.py` |
| Search and additional tests | Tests for title/body matches, case, missing and blank queries, no match, and correct post IDs |
| Login-required decorator and tests | Anonymous add/delete blocked; logout revokes delete access |
| Render and PostgreSQL | `render.yaml`, `Procfile`, environment-driven configuration |
| Lint and formatting | `.flake8`, `pyproject.toml`, GitHub Actions |
| Actual red/green runs | `evidence/01-red-factory.txt`, `02-red-behavior.txt`, `03-green-tests.txt` |

## TDD evidence

Tests were written against the tutorial baseline before the fixes. The first run failed because `create_app` did not exist. After introducing the factory, **21 tests passed and 8 failed**. The failures exposed blank-post acceptance, a missing-post deletion returning success, missing search feedback, invalid search-result IDs, unsafe HTML, oldest-first ordering, and the PostgreSQL driver default. The implementation fixes brought the same behavior checks to green. The PostgreSQL expected URI was updated to explicitly name the installed `psycopg2` driver. These logs are actual local runs, not a claim that the complete original tutorial was re-created from scratch.

## Deployment and TA preparation

The app is deployed at **https://ece444-pra6-6t69.onrender.com/**. The [Render guide](docs/DEPLOYMENT.md) documents how to reproduce the deployment, and the [TA explanation guide](docs/TA_GUIDE.md) explains the application and tests. The [submission checklist](docs/SUBMISSION.md) is a working checklist; its deployment-pending entries predate the successful deployment recorded above.

To finish the PRA:

1. Complete the remaining live checks listed above.
2. Submit **https://github.com/YilingZha233/ece444-pra6** to Quercus.
3. Attend the assigned PRA, demonstrate the live app to the TA, and explain the tests and relevant application components in your own words. Confirm that the TA evaluates the work before the session ends.

The implementation and deployment do not by themselves establish completion of Quercus submission or the TA evaluation.

## Differences from the tutorial

- An application factory applies test configuration before `db.init_app`. Changing the database URI after initialization does not change the already-created engine.
- Tests create real posts before testing deletion, and verify stored rows afterward.
- Search uses `entry.id`, shows no-match feedback, and trims whitespace queries.
- PostgreSQL URLs explicitly select `psycopg2`, avoiding a default-driver mismatch.
- Basic post HTML is sanitized with Bleach before rendering with Jinja's `safe` filter. Titles and search queries remain escaped.
- Deletion uses a dedicated button instead of making every click on a post destructive.
- Admin credentials and the session signing key can come from environment variables.

For compatibility with the assigned tutorial, deletion still uses `GET /delete/<id>` and logout uses GET. This is a course demo: a production application should use state-changing POST/DELETE requests with CSRF protection, user records with hashed passwords, and database migrations instead of relying only on `create_all()`.

## Browser verification

A local Gunicorn browser check verified login, posting, mixed-case body search, deletion from search results, and logout. Screenshots are in `evidence/browser-search.png` and `evidence/browser-delete.png`. The Render deployment is now live. Its deployment logs show successful health checks, and the live browser displays a logged-in session and search results. The screenshots in `evidence/` document the earlier local run, not the deployed site.
