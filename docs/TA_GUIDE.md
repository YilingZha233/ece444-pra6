# Prepare to explain your work

The PRA awards 2 points for completing the activities and 3 for demonstrating understanding. Read the code, run it yourself, and practice explaining these points in your own words.

## A short demonstration

1. Open the deployed home page and log in.
2. Add two posts with different titles and bodies.
3. Search using a word from a title, then a word from a body with different capitalization.
4. Log out. Explain why the create form and Delete buttons disappear and why the server still checks authorization independently.
5. Visit the delete endpoint while logged out and show the 401 JSON response. Verify the post remains.
6. Log back in and delete a post; refresh to show the database change persisted.
7. Show `python -m pytest -v`, the passing GitHub Actions workflow, and one earlier failing run in `evidence/`.

## Request flow

Browser → Render → Gunicorn → Flask route → SQLAlchemy → PostgreSQL. The route returns rendered Jinja HTML, a redirect, or JSON. JavaScript calls the deletion route and reloads after success. Locally the same ORM uses SQLite.

`project/app.py` builds and configures Flask. `project/extensions.py` holds the shared SQLAlchemy extension. `project/models.py` defines a Post row. `project/views.py` handles the routes. Templates turn data into HTML, while static CSS/JavaScript runs in the browser.

## Explain the tests

| Test group | What it proves | Why it matters |
| --- | --- | --- |
| Index, database, empty state | Home responds, schema exists, initial database is empty | A working route alone does not establish a working database |
| Login/logout and invalid login | Valid credentials set a session, invalid ones do not, logout clears it | Covers both success and failure paths |
| Add messages | A logged-in request inserts a row and renders escaped titles/basic HTML | Checks both database state and page output |
| Reject blank/missing fields | Invalid data returns 400 and inserts no row | Avoids unusable entries |
| Delete existing post | Correct row disappears and other rows remain | A JSON success response alone could hide a broken delete |
| Login-required and logout tests | Anonymous deletion is 401 and preserves the row; logout removes access | Tests the decorator's observable behavior |
| Missing/malformed delete IDs | Unknown row returns 404; non-integer IDs do not reach the route | Avoids claiming deletion succeeded when nothing existed |
| Search title/body/case | Only matching entries appear for both fields regardless of capitalization | These are additional tests requested by the tutorial |
| Search blank/no match/IDs | Empty input is handled; no-match feedback exists; result IDs support deletion | Catches template mistakes that a simple status-code test misses |
| Sanitization and escaping | Basic formatting remains; executable markup is removed/escaped | Explains why unrestricted `safe` rendering is unsafe |
| Independent databases | Two app instances do not share data | Prevents a test teardown from deleting application data |
| PostgreSQL URL normalization | Legacy/current URLs select the installed driver | Configuration check only; live connectivity still needs deployment verification |

The suite reports 29 cases because parameterized tests expand one function into multiple inputs. The `client` fixture uses Flask's test client, so requests go through routes without starting a network server. Each `app` fixture uses pytest's `tmp_path` to create a fresh SQLite file, creates tables before the test, then removes the session, drops those temporary tables, and disposes the engine afterward.

## Explain TDD

Red: write a requirement as an automated test and run it to see an expected failure. Green: implement the smallest change that satisfies it. Refactor: improve structure while rerunning the same suite. Here the actual behavior run had 8 failures and 21 passes before fixes; the final run has 29 passes. The earlier factory import failure is separate evidence. The logs do not claim the original tutorial was developed entirely from scratch.

Choose one example to explain concretely: `test_delete_missing_post` expected HTTP 404 but the starter returned 200. The implementation now retrieves the Post, returns 404 when absent, and only deletes a row when it exists.

## Likely questions

**Why an application factory?** SQLAlchemy reads the database URI when initialized. The factory applies the temporary test configuration before `db.init_app`, so tests use the intended database. Changing the URI later does not replace an existing engine.

**What is a session?** Flask's default session stores signed data in a client cookie. The secret key prevents undetected modification; the cookie is not encrypted. We store only a login flag, not the password or database URL.

**Why `@wraps`?** It preserves the wrapped view's metadata and name. The decorator checks the session before allowing the deletion function to run.

**Why check the database after a request?** A route could return success without changing stored data. Querying the row verifies the real result.

**GET versus POST?** GET conventionally reads resources; POST changes state. Login submission and adding a post use POST. This tutorial keeps GET deletion for compatibility, but production deletion should use POST/DELETE and CSRF protection. Cookie SameSite settings are not a complete substitute for CSRF protection.

**What is SQLAlchemy doing?** A model maps Python attributes to table columns. `db.session` tracks objects and transactions. `commit()` persists changes. The integer route converter and ORM avoid concatenating user input into SQL.

**Why Gunicorn?** It is the WSGI application server used for deployment. Flask's built-in server is for development. Gunicorn loads the `app` object from `project.app` and binds to Render's supplied port.

**Why PostgreSQL on Render?** The local SQLite file is not durable on a Free web service across redeploys. A separate PostgreSQL service persists independently while its instance remains available.

**What does `create_all()` do?** It creates missing tables for known models. It preserves data but does not migrate existing table layouts. A production project would use migrations.

**Why return JSON for deletion?** The browser's JavaScript checks the HTTP status and JSON `status`, then refreshes on success or shows an error. It does not remove a post merely because any response arrived.

**What would you improve next?** CSRF-protected state-changing endpoints; hashed per-user accounts; database migrations; database-level search for larger datasets; real PostgreSQL integration tests. Keep the distinction between this course demonstration and a full production system clear.
