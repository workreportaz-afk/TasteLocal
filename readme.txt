# TasteLocal — Local Food Tourism Platform

A starter full-stack scaffold: **Django + Django REST Framework + MySQL** backend,
**React (Vite)** frontend. This is a working foundation, not the finished capstone —
you still need to extend it and produce the documentation evidence the brief requires.

## 1. Setup

### Backend
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

## 2. What's already built

| Layer | What's there |
|---|---|
| Models | `Vendor`, `FoodExperience`, `Booking`, `Review` (core/models.py) |
| API | JWT auth (register/login/refresh), full CRUD for experiences/bookings/reviews/vendors, search + category filter + ordering |
| Permissions | Public read; only the owning vendor can edit their listings; tourists only see/manage their own bookings |
| Frontend | Home (browse/search/filter), Experience detail + booking form, My Bookings, Login/Register, Vendor Dashboard (create listings) |

Test the API directly at `http://127.0.0.1:8000/api/experiences/` once migrated —
you'll get an empty list until you add data via `/admin/` or the Vendor Dashboard.

## 3. What you still need to build/extend

This scaffold deliberately leaves gaps for you to design and implement, since the
assessment is evaluating your own analysis and decisions, not just working code:

- **Geolocation search** ("food spots near me") — the lat/lng fields are on the models;
  add a `?near=lat,lng&radius=...` filter (e.g. with the Haversine formula or a package
  like `django-geoposition` / PostGIS if you switch databases).
- **Itinerary planning** — a new model linking a tourist to an ordered list of experiences.
- **Image uploads from the vendor dashboard** (currently text-only fields wired up).
- **Admin approval workflow** for new vendors (`is_approved` field exists, no UI yet).
- **Payment integration** (e.g., Stripe test mode) if you want end-to-end booking.
- **Automated tests** — `core/tests.py` is not started; add model + API tests
  (`pytest-django` or Django's built-in `TestCase`) for Task 6.

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
brief's technical environment. Note trade-offs (e.g. no built-in geosearch without
extra packages) as feasibility risks.

**Task 3 — Business Case**
Pull risks from what's already flagged above (payment integration, geolocation
complexity, vendor onboarding effort) plus stakeholder pain points (vendor budget/
digital literacy — suggests a simple, guided vendor dashboard, which this scaffold
starts).

**Task 4 — Project Planning**
Turn the "what you still need to build" list above into a schedule with milestones.
A natural phase order: (1) auth + core CRUD [done here], (2) booking flow [done],
(3) reviews [done], (4) geolocation/itinerary, (5) vendor approval + payments,
(6) testing/hardening.

**Task 5 — Solution Development**
Extend this scaffold. Keep a running log/table of stakeholder feedback from your
mentoring sessions and note which model/API/UI changes each item drove — this is
required project evidence.

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
