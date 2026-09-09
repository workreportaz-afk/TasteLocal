# TasteLocal — Local Food Tourism Platform

A starter full-stack scaffold: **Django + Django REST Framework + MySQL** backend,
**React (Vite)** frontend. This is a working foundation, not the finished capstone —
you still need to extend it and produce the documentation evidence the brief requires.

## 1. Setup

You can run this project two ways: **locally** (Python venv + npm, what we've been
using so far) or via **Docker** (recommended once you're past initial development —
one command brings up MySQL, Django and React together, and it's what you'd submit
alongside your code to prove the project runs reproducibly on any machine).

### Option A: Docker (recommended)

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

```bash
cp .env.example .env
# edit .env and set real values for DB_PASSWORD, DB_ROOT_PASSWORD, DJANGO_SECRET_KEY

docker compose up --build
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/api/
- Admin: http://localhost:8000/admin/ (run `docker compose exec backend python manage.py createsuperuser` once, in another terminal, to create a login)
- Seed demo data: `docker compose exec backend python manage.py seed_demo_data`

Migrations run automatically on startup. Both backend and frontend hot-reload on
file changes, same as running them locally — the dev compose file bind-mounts your
source code into the containers.

To stop: `Ctrl+C`, then `docker compose down` (add `-v` to also wipe the MySQL volume).

**Production-style stack** (gunicorn + nginx, no dev servers, `DEBUG=False`):
```bash
docker compose -f docker-compose.prod.yml up --build -d
```
Serves the built frontend on http://localhost (port 80), with nginx reverse-proxying
`/api/`, `/admin/`, `/static/` and `/media/` to the backend container. Useful to
demonstrate the project runs like a real deployed app, not just a dev sandbox.

### Option B: Local (Python venv + npm)

#### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate            # Windows
# source venv/bin/activate       # Mac/Linux

pip install -r requirements.txt

# Create the MySQL database first (in MySQL Workbench / CLI):
#   CREATE DATABASE tastelocal_db CHARACTER SET utf8mb4;

copy .env.example .env           # Windows: copy, Mac/Linux: cp
# then edit .env with your MySQL username/password

python manage.py makemigrations core
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
API now runs at `http://127.0.0.1:8000/api/`. Admin at `/admin/`.

### Frontend
```bash
cd frontend
npm install
npm run dev
```
App runs at `http://localhost:5173`.

## 2. GitHub setup

If you haven't already:

1. Create a **new, empty** repository on GitHub (no README/license/gitignore — you already have those here).
2. From your project root (`D:\TasteLocal`):
   ```bash
   git init
   git add .
   git commit -m "Initial commit: TasteLocal capstone scaffold"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<your-repo-name>.git
   git push -u origin main
   ```
3. **Double-check `backend/.env` and root `.env` are NOT in your commit** — run `git status` before committing; they should be absent (the `.gitignore` here excludes them). Only `.env.example` files should ever be committed. If you ever accidentally commit a real password, rotate it immediately — removing it from a later commit doesn't remove it from git history.

Once pushed, the `.github/workflows/ci.yml` pipeline will automatically run on every push: it spins up a real MySQL instance, runs Django migrations and tests, builds the React production bundle, and builds both Docker images — so you (and your mentor, if they check the repo) get an automatic pass/fail signal that the project actually works, not just "works on my machine."

For subsequent changes:
```bash
git add .
git commit -m "Describe what changed"
git push
```

## 2. What's already built

| Layer | What's there |
|---|---|
| Models | `Vendor`, `FoodExperience`, `Booking`, `Review`, `SavedExperience`, `ItineraryStop` (core/models.py) |
| API | JWT auth (register/login/refresh/me), full CRUD for experiences/bookings/reviews/vendors/saved-spots/itinerary, search + category filter + ordering, geolocation "near me" search |
| Permissions | Public read (approved vendors only); vendors edit only their own listings and can see their own pending listings; tourists only see/manage their own bookings/saved/itinerary |
| Roles | Three roles computed server-side: `admin` (Django staff/superuser), `vendor` (has a Vendor profile), `tourist` (everyone else) — returned by `/api/auth/me/` as `role`. Frontend gates pages by role (Vendor Dashboard is vendor-only, Saved/Trip/Bookings are tourist-only, admins can access everything) via `RequireRole` |
| Vendor approval | Unapproved vendors' listings are hidden from public browsing but visible to the vendor themselves; new vendors self-register as unapproved and must be approved via Django admin (`Vendor.is_approved`) |
| Geolocation | Free "near me" search via the haversine formula (`core/geo.py`, no external API) + free address-to-coordinates lookup via OpenStreetMap's Nominatim in the Vendor Dashboard |
| Maps | Free OpenStreetMap + Leaflet map on each experience detail page, no API key |
| Image uploads | Vendors can attach a photo when publishing a listing (multipart upload, Pillow-backed) |
| Frontend | Home (browse/search/filter/near-me), Experience detail (booking, save, add-to-trip, map, reviews), My Bookings, Saved Spots, Plan My Trip, Login/Register, Vendor Dashboard (create listings with image + geocoding) |
| Internationalization | English, Simplified Chinese, and Bahasa Melayu via `react-i18next`, with a language switcher in the navbar. Choice persists across visits (localStorage). All pages fully translated: navbar, homepage, experience detail, bookings, saved spots, plan my trip, vendor dashboard, login/register, and role-restricted messaging — see `src/i18n/locales/` |
| Content translation | Experience titles/descriptions are machine-translated on first view per language via the free MyMemory API (no key needed), then cached in `FoodExperienceTranslation` so each experience is only translated once, ever, per language — see `core/translation.py`. Vendor/business names stay in English intentionally (proper nouns). Falls back silently to English if the translation API is unreachable. **Includes a circuit breaker**: once one translation call fails (e.g. MyMemory's free daily quota — a few thousand words — is exhausted), all further translation attempts skip the network entirely for 30 minutes and fall back to English immediately. Without this, a homepage of N experiences would retry a failing API N times on every single page load; this is a real incident this project hit during development, not a hypothetical — see `TranslationCachingTests.test_circuit_breaker_stops_hammering_a_failing_api` |
| Recommendations ("Recommended For You") | Content-based ranking from the tourist's own saved/booked/itinerary history (category preference matching), with a highest-rated fallback for new users with no history. **Not** a machine-learning model or external AI call — see `core/recommendations.py` for the honest explanation. `GET /api/experiences/recommended/` |
| AI Trip Planner (chat) | A conversational-feeling assistant that parses free-text messages for category/area/budget keywords, then filters and ranks real experiences. **This is rule-based keyword matching, not a large language model** — no external AI API is called, and this is documented plainly in the UI disclaimer and in `core/trip_planner.py`. A genuine LLM-backed version would need a paid API key (OpenAI/Anthropic/etc.) — there's no free equivalent, unlike MyMemory/Nominatim elsewhere in this project. `POST /api/experiences/plan-trip/` |
| Tests | `core/tests.py` — model logic, API auth enforcement, geolocation radius filtering, saved/itinerary CRUD, vendor approval gating (26 tests, all passing as of last run) |
| Infrastructure | Docker (dev + production-style compose with gunicorn/nginx), GitHub Actions CI (runs tests against real MySQL, builds both images) |
| Demo data | `seed_demo_data` management command — real Singapore Michelin Bib Gourmand hawker stalls, mock tourists, completed bookings, reviews |

Test the API directly at `http://127.0.0.1:8000/api/experiences/` once migrated —
you'll get an empty list until you add data via `/admin/`, the Vendor Dashboard, or
`python manage.py seed_demo_data`.

## 3. What you still need to build/extend

The core is functional end-to-end, but a few things remain deliberately open —
either genuinely out of scope for a coursework MVP, or good candidates for you
to design and document as your own contribution:

- **Payment integration** (e.g., Stripe test mode) if you want end-to-end paid booking rather than a "request to book" flow.
- **Admin approval UI for vendors** — currently done via Django admin (`is_approved` checkbox), which is functional but not a dedicated in-app moderation screen.
- **Distance accuracy** — "near me" uses straight-line (haversine) distance, not actual walking/driving distance. Fine for an MVP; worth naming as a known limitation in your Task 6 evaluation.
- **Restaurant vs. Food Tour vs. Café as distinct top-level nav sections** (rather than just category filters) if you want to mirror competitor sites more closely.

## 4. Mapping this scaffold to the 7 project tasks

The brief grades documentation as heavily as code — treat each task below as a
deliverable, not just a coding step.

**Task 1 — Requirements Elicitation & Business Process Analysis**
Use the four stakeholder interviews in the brief. Draft a problem statement, then
write functional requirements (e.g. "vendor can list an experience", "tourist can
book and review") directly against the models here — each model field should trace
back to a stated need. Document this as a requirements table.

**Task 2 — Scoping & Feasibility**
This stack (Django REST Framework + MySQL + React) *is* your tool recommendation —
write up why: Django's ORM/admin cuts backend dev time, DRF gives you a REST API
for React and future mobile apps, MySQL is free/well-supported and matches the
brief's technical environment. Note the geolocation trade-off as a feasibility
decision you made: haversine-in-Python (free, simple, no extra infra) vs. MySQL
spatial indexes or Google's Distance Matrix API (more accurate, more setup/cost).

**Task 3 — Business Case**
Pull risks from what's already flagged above (payment integration not yet built,
straight-line vs. real-world distance accuracy, vendor onboarding effort) plus
stakeholder pain points (vendor budget/digital literacy — suggests a simple,
guided vendor dashboard, which this scaffold has, including free geocoding so
vendors never need to know their own coordinates).

**Task 4 — Project Planning**
Turn the "what you still need to build" list above into a schedule with milestones.
A natural phase order: (1) auth + core CRUD [done], (2) booking flow [done],
(3) reviews [done], (4) geolocation/itinerary/saved-spots [done], (5) vendor
approval [done], (6) Docker/CI infrastructure [done], (7) payments, (8) final
testing/hardening.

**Task 5 — Solution Development**
Extend this scaffold. Keep a running log/table of stakeholder feedback from your
mentoring sessions and note which model/API/UI changes each item drove — this is
required project evidence. (One real example from this project's own build log:
an early version had a bug where a queryset annotation collided with a model
property name, silently risking a crash on the experience listing endpoint —
caught by writing a regression test, not by manual testing. Worth citing as a
concrete example of why Task 6's testing matters.)

**Task 6 — Testing & Evaluation**
Add unit tests for serializers/models (e.g. `Booking.total_price` auto-calculation),
integration tests for the booking API, and manual UAT scripts (e.g. "tourist searches
for street food, books, leaves a review"). Record results in a comparison table
against the objectives in the brief.

**Task 7 — Project Closure**
Status report on which of the 7 tasks/features are complete vs. pending, an
acceptance criteria checklist (map each to a requirement from Task 1), and a
sign-off form template.

## 5. Suggested folder for your documentation

Keep your Word/PowerPoint deliverables alongside the code so everything submits
together, e.g.:
```
docs/
  01-requirements-and-analysis.docx
  02-feasibility-and-tools.docx
  03-business-case.docx
  04-project-charter-and-schedule.docx
  05-stakeholder-feedback-log.xlsx
  06-test-plan-and-results.docx
  07-status-report-and-signoff.docx
```
