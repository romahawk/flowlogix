# FlowLogix – Supply Tracker Dashboard

FlowLogix is a web application for managing and tracking pharma supply orders.
It started as an internal tool for a **pharmaceutical logistics company** and
also serves as a case study of how I use **Agile project management** together
with **full-stack development**.

---

## 🔗 Live Demo

> **Note:** hosted on a free tier, cold starts may take 30–60 seconds.

- 🌐 **Demo URL:** https://flowlogix.onrender.com/dashboard

---

## 📦 Features

- Orders dashboard with filters, sorting, and pagination.
- Order timeline visualization (ETD → ETA / ATA) using Chart.js.
- Warehouse and Delivered views for different lifecycle stages.
- User authentication and session management (Flask-Login).
- Dark mode and responsive layout (Tailwind).
- Utility scripts to seed demo data and maintain the database.

---

## 🧩 Tech Stack

**Backend**

- Python, Flask
- SQLAlchemy + SQLite
- Flask-Login (auth)
- Flask-Migrate / Alembic (migrations)

**Frontend**

- HTML templates (Jinja2)
- Tailwind CSS
- Vanilla JavaScript
- Chart.js (timeline / visualization)

**Other**

- Git & GitHub
- Render / similar PaaS for deployment

---

## 🧭 Architecture (high level)

- `app/` – main Flask application package  
  - `routes/` – route modules for dashboard, warehouse, delivered, admin, etc.  
  - `templates/` – page templates and modals  
  - `static/` – JS, CSS, images, uploads  
  - `utils/` – backend helpers (database, models, roles, decorators, seeding)
- `data/` – local database / data files (dev)
- `migrations/` – database migration scripts
- `utils/` – standalone maintenance scripts (backup, import, cleanup)
- `run.py` / `wsgi.py` – entrypoints for local dev and production

See `docs/ARCHITECTURE.md` for a more detailed description.

---

## 🚀 Running Locally

### 1. Clone the repo

```bash
git clone https://github.com/romahawk/flowlogix.git
cd flowlogix
```
### 2. Create & activate virtual environment

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env  # on Windows: copy .env.example .env
```

### 5. Initialize database (if required)

```bash
flask db upgrade      # if using Flask-Migrate
# or run your seed script
python utils/import_orders.py
```

### 6. Run the app

```bash
python run.py
<<<<<<< HEAD
```
=======
```
>>>>>>> 984c2f7d744f643c8ad9ecca702b4c040353cc5d
