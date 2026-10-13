# Syslog ML Analytics — Web App

FastAPI + Postgres backend, React (Vite + TypeScript) frontend. Provides
device/credential management, log search, and a semantic-search Log
Assistant now, with an ML feedback/correction loop planned as a later phase
(see "Roadmap" below).

## Log search

The "Log search" page (`/logs`) is a filterable, paginated view over
`syslog_ml.events` in ClickHouse — read-only, available to any
authenticated user (same access level as the Devices page). Filters:
time range (1h/24h/7d/30d), source IP (exact), hostname/program/message
(case-insensitive substring), severity and predicted category (exact),
and an anomalies-only toggle.

- **Backend**: `GET /api/logs/search` (`app/api/routes/logs.py`,
  `app/services/log_search_service.py`). Every filter is bound as a
  ClickHouse query parameter, never string-interpolated. Substring
  filters use `positionCaseInsensitive(col, %(param)s) > 0` rather than
  `... ILIKE %(param)s`: tested directly against a real ClickHouse
  instance during development, `ILIKE` let an unescaped `%`/`_` in the
  search term act as a LIKE wildcard (searching `100%` would silently
  misinterpret the `%`), and separately isn't available on every
  ClickHouse version still in the wild. `positionCaseInsensitive` treats
  the parameter as a literal substring, so neither issue applies, and it
  was confirmed to behave identically otherwise (case-insensitivity,
  pagination, and combined filters all verified against seeded rows in a
  real ClickHouse before this was committed).
- Pagination is two queries (a `count()` and a `LIMIT`/`OFFSET` page),
  each bounded (`page_size` capped at 500, `hours` capped at 90 days —
  matching `events`' own TTL).

## Log Assistant

The "Log Assistant" page (`/assistant`) is a chat-style interface for asking
natural-language questions about recent syslog events ("any auth failures on
core-switch-1 today?"). It answers using retrieval-augmented generation, not
the model's own general knowledge:

1. The question is embedded (Ollama's `/api/embeddings`, model
   `nomic-embed-text` by default) and matched by cosine similarity (OpenSearch
   `knn`) against event embeddings.
2. The top matches (`TOP_K = 8`) are given to a local chat model (Ollama,
   `llama3.2:3b-instruct-q4_K_M` by default -- small, CPU-only inference) as
   the *only* evidence it's allowed to use, with an explicit instruction to
   say so when the excerpts don't answer the question rather than guess. This
   matches the pipeline's existing "nothing pretends to know a hostname it
   doesn't" philosophy (see the top-level `syslog-ml-analytics/README.md`).
3. The response includes both the generated answer and the raw source log
   entries it was based on, shown collapsed under the answer in the UI.

The embeddings themselves are produced separately, not by the web app: a new
periodic worker, `ml/log_assistant_indexer.py` (run via
`syslog-ml-indexer.timer`, same oneshot+timer pattern as the SNMP resolver,
every 5 minutes), reads newly-arrived `syslog_ml.events` rows from
ClickHouse, embeds each message, and bulk-indexes them into OpenSearch.
Keeping this out of the hot ingestion path (`ml/consumer.py`) matters the
same way it does for SNMP resolution: embedding calls are slow enough on
CPU-only hardware that they can't sit in line with real-time log processing.

- **Backend**: `POST /api/log-assistant/ask` (and `/search` for retrieval
  without generation) in `app/api/routes/log_assistant.py` /
  `app/services/log_assistant_service.py`. New config fields in
  `app/core/config.py` (`SYSLOG_ML_OLLAMA_HOST`,
  `SYSLOG_ML_OLLAMA_CHAT_MODEL`, `SYSLOG_ML_OLLAMA_EMBED_MODEL`,
  `SYSLOG_ML_OPENSEARCH_HOST`, etc.) follow the same env-var-override
  convention as everything else in `Settings`.
- **New infrastructure**: this is the first feature in the project to need
  OpenSearch and Ollama -- neither is required for the rest of the pipeline
  or web app. See "Production install" below for setup; both are optional
  (the rest of the app works fine without them, same as log search works
  without the resolver's SNMP credentials being configured).
- **No stable event ID to link back to**: `syslog_ml.events` has no
  `event_id` column, so a "source" shown by the assistant can't deep-link
  into the Log search page the way a real identifier would -- it's
  rendered as plain text (time/hostname/severity/program/message) instead.

## Why this stack

- **FastAPI**: shares Python with the rest of the pipeline (`ml/`), async,
  typed, and gives an OpenAPI schema for free.
- **Postgres**, separate from ClickHouse: the web app's own state (users,
  SNMP credentials, audit log, ML feedback) is comparatively small,
  relational, and needs transactional writes — a poor fit for ClickHouse,
  which stays dedicated to the high-volume append-only log events.
- **SNMP credentials moved from a CSV file into this database**: same
  "opt-in, never guessed" principle as before, now with an admin-only UI,
  encryption at rest (Fernet), and an audit trail instead of a flat file
  anyone with VM access could read in plaintext. `ml/device_resolver.py`
  reads from this same table now — one source of truth.
- **React SPA**: the app has real interactive state (forms, filters, role-
  gated views) that suits client-side routing better than server-rendered
  pages.

## Structure

```
web/
  backend/
    app/
      core/       # config, JWT + bcrypt auth, Fernet encryption for secrets
      db/         # SQLAlchemy async models (users, snmp_credentials, ...)
      schemas/    # Pydantic request/response models
      services/   # business logic, separated from route handlers
      api/routes/ # thin FastAPI route handlers
      clickhouse_client.py
      opensearch_client.py  # Log Assistant: lazy OpenSearch client
      ollama_client.py      # Log Assistant: async Ollama HTTP client (embed + chat)
    migrations/   # Alembic
    scripts/create_admin.py   # bootstrap the first admin account
  frontend/
    src/
      api/        # typed API client (axios)
      auth/       # AuthContext (JWT storage, login/logout)
      components/ # Layout, ProtectedRoute (role-gated)
      pages/      # Login, Devices, Credentials, LogSearch, LogAssistant
    e2e/smoke.mjs         # Playwright smoke test of the real auth/RBAC/CRUD flow
    e2e/log_assistant.mjs # Playwright test of the chat page (mocks only the Ollama/OpenSearch-backed /ask call)
  systemd/        # production unit for the API (gunicorn+uvicorn workers)
  nginx/          # reverse proxy + static SPA serving config
```

## Local development

Backend:

```bash
cd web/backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
# Postgres running locally with a syslog_ml DB/user (see Step 1 below)
export SYSLOG_ML_DATABASE_URL=postgresql+asyncpg://syslog_ml:syslog_ml@localhost:5432/syslog_ml
.venv/bin/alembic upgrade head
.venv/bin/python scripts/create_admin.py --username admin
.venv/bin/uvicorn app.main:app --reload --port 8000
```

Frontend (separate terminal):

```bash
cd web/frontend
npm install
npm run dev   # http://localhost:5173, proxies /api to :8000 (see vite.config.ts)
```

Smoke test (with both servers running):

```bash
cd web/frontend
ADMIN_USERNAME=admin ADMIN_PASSWORD=<the password you set> npm run test:e2e
```

## Production install (Ubuntu/Debian, continuing from the pipeline's own README)

Assumes Step 1 (service account/directories) from the top-level
`syslog-ml-analytics/README.md` is already done.

### 1. Install Postgres

```bash
sudo apt-get install -y postgresql
sudo -u postgres psql -c "CREATE USER syslog_ml WITH PASSWORD '<pick a real password>';"
sudo -u postgres psql -c "CREATE DATABASE syslog_ml OWNER syslog_ml;"
```

### 2. Deploy the backend

```bash
sudo cp -r web/backend /opt/syslog-ml/web/backend
cd /opt/syslog-ml/web/backend
sudo python3 -m venv .venv
sudo .venv/bin/pip install -r requirements.txt

sudo cp systemd/web-api.env.example /etc/syslog-ml/web-api.env   # from repo root's web/systemd/
sudo $EDITOR /etc/syslog-ml/web-api.env   # fill in real secrets
sudo chmod 600 /etc/syslog-ml/web-api.env
sudo chown syslog-ml:syslog-ml /etc/syslog-ml/web-api.env /opt/syslog-ml/web/backend -R

# Run the migration and create the first admin as the syslog-ml user so
# file ownership stays consistent:
sudo -u syslog-ml SYSLOG_ML_DATABASE_URL=postgresql+asyncpg://syslog_ml:<password>@localhost:5432/syslog_ml \
  /opt/syslog-ml/web/backend/.venv/bin/alembic upgrade head
sudo -u syslog-ml SYSLOG_ML_DATABASE_URL=postgresql+asyncpg://syslog_ml:<password>@localhost:5432/syslog_ml \
  /opt/syslog-ml/web/backend/.venv/bin/python scripts/create_admin.py --username admin
```

**Checkpoint** — confirm `alembic upgrade head` reports success and the admin script prints a user ID.

### 3. Wire up the API systemd service and the resolver's shared credentials

```bash
sudo cp web/systemd/syslog-ml-web-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now syslog-ml-web-api

# The resolver (from the pipeline README) needs the SAME database and
# encryption key as the web app:
sudo cp systemd/syslog-ml-resolver.env.example /etc/syslog-ml/resolver.env   # from repo root's systemd/
sudo $EDITOR /etc/syslog-ml/resolver.env   # DATABASE_URL + CREDENTIAL_ENCRYPTION_KEY, matching web-api.env
sudo chmod 600 /etc/syslog-ml/resolver.env
sudo chown syslog-ml:syslog-ml /etc/syslog-ml/resolver.env
sudo systemctl restart syslog-ml-resolver.timer   # if already running from before
```

**Checkpoint:** `curl http://127.0.0.1:8000/api/health` should return `{"status":"ok"}`.

### 4. Build and serve the frontend

Ubuntu 22.04's default `apt install nodejs` gives you Node 12.x from the
Ubuntu archive — too old for this frontend's build tooling (Vite 8), which
I confirmed by checking what Vite actually requires. Install a current
Node LTS from NodeSource instead (`deb.nodesource.com` is blocked from
this sandbox too, so the exact command below is from training data, not a
live check — if it 404s or errors, NodeSource's current setup instructions
are the fallback):

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
node --version   # should print v20.x, not v12.x
```

Then build and deploy:

```bash
sudo apt-get install -y nginx
cd web/frontend
npm ci
npm run build
sudo mkdir -p /opt/syslog-ml/web/frontend
sudo cp -r dist /opt/syslog-ml/web/frontend/dist

sudo cp web/nginx/syslog-ml-web.conf /etc/nginx/sites-available/syslog-ml-web
sudo ln -s /etc/nginx/sites-available/syslog-ml-web /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

**Checkpoint** — open `http://<vm-ip>/` and confirm the login page loads,
then log in with the admin account from Step 2.

### 5. Log Assistant (optional): OpenSearch, Ollama, and the indexer timer

Skip this step if you don't need the chat assistant -- the rest of the app
works fine without it. I could not verify any of the commands in this step
against real OpenSearch/Ollama install docs (both domains are blocked from
this sandbox); treat them as a starting point, not a confirmed-working
sequence, the same honesty flag already on the ClickHouse/Grafana steps in
the top-level `syslog-ml-analytics/README.md`.

```bash
# OpenSearch (single-node, no security plugin -- same trust boundary as
# ClickHouse: localhost-only, no auth. Put a firewall/reverse proxy in front
# of it if that's not true in your deployment.)
curl -fsSL https://artifacts.opensearch.org/publickeys/opensearch.pgp | sudo gpg --dearmor -o /usr/share/keyrings/opensearch-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/opensearch-keyring.gpg] https://artifacts.opensearch.org/releases/bundle/opensearch/2.x/apt stable main" | sudo tee /etc/apt/sources.list.d/opensearch.list
sudo apt-get update
sudo apt-get install -y opensearch
# Disable the security plugin for a localhost-only dev/trusted deployment,
# or configure it properly -- see OpenSearch's own docs for your situation.
sudo systemctl enable --now opensearch

# Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull nomic-embed-text               # embeddings, must match SYSLOG_ML_OLLAMA_EMBED_MODEL
ollama pull llama3.2:3b-instruct-q4_K_M    # chat, must match SYSLOG_ML_OLLAMA_CHAT_MODEL
```

**Checkpoint** — `curl http://localhost:9200` returns a JSON cluster info
response; `curl http://localhost:11434/api/tags` lists both pulled models.

Add the Log Assistant env vars to the same `/etc/syslog-ml/web-api.env` from
Step 2 (`SYSLOG_ML_OLLAMA_HOST`, `SYSLOG_ML_OLLAMA_CHAT_MODEL`,
`SYSLOG_ML_OLLAMA_EMBED_MODEL`, `SYSLOG_ML_OPENSEARCH_HOST`, etc. -- see
`app/core/config.py` for the full list and defaults), then restart the API:

```bash
sudo systemctl restart syslog-ml-web-api
```

Then wire up the indexer timer (from the repo root's `systemd/`, alongside
the resolver):

```bash
sudo cp systemd/syslog-ml-indexer.service systemd/syslog-ml-indexer.timer /etc/systemd/system/
sudo cp systemd/syslog-ml-indexer.env.example /etc/syslog-ml/indexer.env
sudo $EDITOR /etc/syslog-ml/indexer.env   # only needed if you changed a default above
sudo chmod 600 /etc/syslog-ml/indexer.env
sudo chown syslog-ml:syslog-ml /etc/syslog-ml/indexer.env
sudo systemctl daemon-reload
sudo systemctl enable --now syslog-ml-indexer.timer
```

**Checkpoint:**

```bash
sudo systemctl start syslog-ml-indexer   # run once immediately, don't wait for the timer
sudo journalctl -u syslog-ml-indexer -n 50
curl -s http://localhost:9200/syslog_logs/_count   # should be > 0 once events exist
```

Once some events are indexed, log in and ask the Log Assistant a question
about recent traffic you know occurred.

## Honest limitations

- No TLS in the provided nginx config — this handles login credentials and
  SNMP secrets, so put it behind HTTPS (a reverse proxy with certbot, or
  your existing TLS termination) before exposing it beyond a trusted
  network. I didn't set this up because I don't know your domain/cert
  situation.
- Tested in this session against a real local Postgres and a real browser
  (Playwright) for the full auth/RBAC/credential-CRUD/persistence flow, and
  again for the Log Assistant page (login, navigation, asking a question,
  rendering the answer and its sources, clearing input state, and the
  upstream-error path) — not tested against a live ClickHouse, OpenSearch,
  or Ollama (none available in this sandbox), so the Devices page's actual
  data rendering and the Log Assistant's real embedding/retrieval/generation
  quality are both unverified until you run them against your real
  ClickHouse/OpenSearch/Ollama instances. The `/ask` endpoint itself
  (routing, request/response shapes, 502 handling) was only verified by
  mocking that one HTTP call from the browser side — the backend code that
  actually talks to OpenSearch and Ollama has not been exercised against
  real servers.
- The Log Assistant's answer quality depends entirely on embedding and chat
  model choice, neither of which has been tuned or evaluated here — treat
  early answers the same way `ml/labeling_rules.py`'s weak-supervision
  category guesses are treated: a starting point, not verified fact.
- Password reset / account recovery isn't built — the only way to regain
  access if the sole admin's password is lost is `scripts/create_admin.py`
  won't help (it refuses existing usernames) or a manual DB update.

## Roadmap (not yet built)

- **ML feedback loop**: the `classification_feedback` table already exists
  (see `app/db/models.py`) but has no API/UI yet — review predicted
  categories, correct wrong ones, feed corrections back into
  `ml/train_classifier.py`.
