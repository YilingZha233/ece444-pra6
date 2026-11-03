# Deploy on Render

## 1. Create your account

Register at https://dashboard.render.com/register using your UofT email, as specified in the PRA. Complete account verification yourself. Never commit your database URL, admin password, or secret key.

## 2. Recommended: deploy the included Blueprint

After the code is in `YilingZha233/ece444-pra6`:

1. In Render, select **New → Blueprint** and select this repository. If prompted, connect GitHub and grant access to this repository.
2. Render reads `render.yaml` from the repository root. Review that both `ece444-pra6` and `ece444-pra6-db` use the **Free** plan. Use the same region for both resources. If Free is unavailable or Render proposes a charge, stop and review the options before proceeding.
3. Set the requested `ADMIN_PASSWORD` to a password of your choice, directly in Render. The Blueprint generates `SECRET_KEY` and connects `DATABASE_URL` to the database automatically. `ADMIN_USERNAME` is `admin`.
4. Deploy the Blueprint. The startup command creates missing tables before Gunicorn starts. It does not delete existing entries.
5. Wait for the web service to show **Live**. Open the URL shown by Render; do not guess the URL from the service name.

Blueprint values:

| Setting | Value |
| --- | --- |
| Runtime | Python |
| Python | 3.12.14 |
| Build | `pip install -r requirements.txt` |
| Start | `python create_db.py && gunicorn project.app:app --bind 0.0.0.0:$PORT` |
| Health check | `/health` |
| Database | Render PostgreSQL, connected through `DATABASE_URL` |

## 3. Alternative: create resources manually

If you prefer the tutorial's manual flow:

1. Select **New → Postgres**. Choose the Free plan and region. Wait until it is available.
2. Select **New → Web Service**, connect your repository, and use branch `main`. Keep the root directory empty.
3. Select Free and use the build/start commands in the table above.
4. Set these environment variables in the web service before deploying:
   - `PYTHON_VERSION`: `3.12.14`
   - `DATABASE_URL`: the database's **Internal Database URL**
   - `SECRET_KEY`: generate a random secret using Render's secret generator
   - `ADMIN_USERNAME`: `admin`
   - `ADMIN_PASSWORD`: your chosen demo password
5. Set `/health` as the health-check path and deploy.

The web service and PostgreSQL database must be in the same region for internal connectivity. If you create tables locally instead, use the External Database URL only in your local environment. On macOS/zsh the syntax is `export DATABASE_URL='...'`; the tutorial's `$env:DATABASE_URL=...` is PowerShell syntax. The provided start command handles schema creation, so local remote-database initialization is unnecessary.

## 4. Verify the live deployment

Use the actual live URL from Render for all of these checks:

1. Open `/health`: expect `{"status":"ok"}`.
2. Open the home page; log in with `admin` and your Render password.
3. Add `PRA6 deployment check` with body `Flask on PostgreSQL`.
4. Search for `pOsTgReSqL`: the entry must appear.
5. Refresh the page: the post must remain.
6. Log out: the new-entry form and Delete buttons must disappear.
7. Try `/delete/<the actual post ID>` while logged out: expect HTTP 401 and JSON status 0; the post must still exist.
8. Log back in and delete the test post using its Delete button. Refresh and search again: it must be absent.
9. For stronger persistence evidence, add another disposable demo entry, restart or redeploy the service, and verify it remains. This distinguishes remote PostgreSQL persistence from an ephemeral SQLite file.
10. Record the URL and results in `docs/SUBMISSION.md`. Do not include secrets.

## Troubleshooting

- **Missing table**: confirm the start command includes `python create_db.py &&` before Gunicorn.
- **Cannot import app**: use `project.app:app`, not `app:app`.
- **Cannot connect to database**: check service/database region and `DATABASE_URL`; never paste the full URL into a public issue.
- **Missing psycopg**: the code normalizes PostgreSQL URLs to `postgresql+psycopg2://`; deploy the final code and pinned dependencies.
- **HTTP 500 after expiry**: check whether the Free PostgreSQL instance expired.
- **First request is slow**: Free web services can spin down while idle; wait for startup before the TA demo.

Render currently documents a **30-day** lifetime for Free PostgreSQL databases, followed by a 14-day upgrade grace period. The assigned tutorial's 90-day statement is outdated. Confirm the current plan information in Render when you deploy.

Official references: [Flask deployment](https://render.com/docs/deploy-flask), [Blueprints](https://render.com/docs/infrastructure-as-code), [Blueprint reference](https://render.com/docs/blueprint-spec), [Python versions](https://render.com/docs/python-version), [Free services](https://render.com/docs/free).
