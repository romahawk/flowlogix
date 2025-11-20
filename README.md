# FlowLogix – Supply Tracker Dashboard

FlowLogix is a web application for managing and tracking pharma supply orders.
It started as an internal tool for **Pharmaceutical logistics company** and also serves as a
case study of how I use **Agile project management** together with
**full-stack development**.

## Features

- Orders dashboard with filters, sorting, and pagination.
- Order timeline visualization (ETD → ETA / ATA) using Chart.js.
- Warehouse and Delivered views.
- User authentication (Flask-Login).
- Dark mode and responsive layout.

## Tech Stack

- **Backend**: Python, Flask, SQLAlchemy, Flask-Login
- **Database**: SQLite (local dev)
- **Frontend**: HTML, Tailwind CSS, vanilla JavaScript, Chart.js

## Documentation

More details are in the `docs/` folder:

- `docs/ARCHITECTURE.md` – high-level architecture
- `docs/AGILE_CASE_STUDY.md` – how I use Agile on this project
- `docs/SPRINTS/` – sprint notes
- `docs/ROADMAP.md` – future plans

## Running Locally (short)

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
pip install -r requirements.txt
python run.py
