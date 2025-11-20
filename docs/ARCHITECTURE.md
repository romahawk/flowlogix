# FlowLogix – Architecture Documentation

FlowLogix is a monolithic Flask-based web application designed for tracking
pharmaceutical supply orders across multiple lifecycle stages.  
This document describes the system architecture, key components, data flow, and
design decisions.

---

# 1. High-Level Overview

FlowLogix follows a **modular monolithic architecture**:

- **Backend:** Python + Flask
- **Frontend:** Jinja2 templates, Tailwind CSS, vanilla JavaScript, Chart.js
- **Database:** SQLite (development/demo), easily replaceable with PostgreSQL
- **Deployment:** WSGI (Gunicorn) via Render/Heroku-style process

The application is organized around four core domains:

1. **Dashboard** – In-process shipments
2. **Warehouse** – Goods that have arrived and awaiting dispatch
3. **Delivered** – Completed orders
4. **Stockreport** – Detailed cargo tracking inside the warehouse

---

## 2. Directory Structure

```text
flowlogix/
├── app/
│   ├── __init__.py
│   ├── routes/
│   ├── templates/
│   ├── static/
│   └── utils/
├── data/
├── docs/
├── migrations/
├── utils/
├── run.py
├── wsgi.py
├── requirements.txt
├── Procfile
└── runtime.txt

---

# 3. Application Layers

FlowLogix cleanly separates responsibilities into layers.

---

## 3.1 Backend Layer (Flask)

### **Entrypoints**
- `run.py` – local development server.
- `wsgi.py` – used by Gunicorn/Render in production.

### **App Factory**
Located in `app/__init__.py`.  
Responsible for:

- creating the Flask app instance
- loading configuration
- initializing:
  - SQLAlchemy (`db`)
  - Flask-Login (`login_manager`)
  - Migrations (`migrate`)
- registering routes blueprints

This follows a scalable pattern for future API separation.

---

## 3.2 Database Layer (SQLAlchemy)

Main models stored in `app/utils/models.py`:

### **User**
- id, email, password hash  
- role (admin, company user, read-only)  
- company relation (future multi-tenant support)

### **Order**
Represents all shipment lifecycle data:

- order number
- product, buyer, responsible
- quantity
- ETD, ETA, ATA
- transit status (`in_process`, `arrived`, `delivered`)
- shipping/transport method

### **StockreportEntry** (planned)
- cargo status inside warehouse  
- timestamps for arrived/stocked/delivered  
- links to order via foreign key

### **Design goals**
- Minimal schema for PoC
- Expandable into multi-model logistics platform
- Clean separation between order lifecycle and warehouse events

---

## 3.3 Routing Layer

Routes are grouped by domain under `app/routes/`.

### **Dashboard Routes**
- Main table & timeline (Chart.js)
- Sorting, filtering by role/company
- Edit order modal

### **Warehouse Routes**
- Show goods currently in warehouse
- Edit warehouse-specific attributes
- Transition to Delivered

### **Delivered Routes**
- Read-only view of all completed shipments
- Delivery analytics (basic)

### **Stockreport Routes**
- Arrived / Stocked / Delivered breakdown
- Modal-based CRUD
- Full cargo traceability

### **Admin Routes** (optional)
- User management
- User-company assignment

---

## 3.4 Template Layer (Jinja2)

All UI renders through server-side templates.

### **Base Layout**
- `base.html` and `base_clean.html`
- Provides navbar, theme toggle, and layout wrappers

### **Modals**
Files like:
- `edit_order.html`
- `edit_warehouse.html`
- `edit_stockreport.html`

are injected dynamically via JS.

### **Dark Mode**
- Implemented via Tailwind classes  
- User preference stored locally (JS + localStorage)

---

## 3.5 Frontend JavaScript Layer

Located in `app/static/js/`.

### **Dashboard logic**
- table sorting
- filtering
- highlighting delays
- timeline coordination

### **Chart.js Timeline**
- Each shipment becomes a horizontal bar from ETD → ETA/ATA
- Color-coded:
  - blue → in process  
  - yellow → en route  
  - green → arrived/delivered  

### **Modal Logic**
- open/close animations
- form population
- AJAX-like behavior (classic HTML submit after safe editing)

---

# 4. Data Flow


Example: Editing an order

1. User clicks **Edit**
2. JS opens modal and loads order ID
3. Flask route fetches order from DB
4. Form submits changes via POST
5. SQLAlchemy updates the record
6. Dashboard reloads with updated timeline + table row

---

# 5. Configuration & Environment

### **`.env` file contains:**
- SECRET_KEY
- DATABASE_URI (default: SQLite)
- ADMIN credentials (optional)
- HOST/PORT config for deployment

### **Deployment**
- `Procfile` defines Gunicorn command:
web: gunicorn wsgi:app
- `runtime.txt` ensures Python version consistency

Works seamlessly with Render, Railway, Fly.io, or Heroku.

---

# 6. Security & Access Control

### **Authentication**
- Flask-Login session-based auth
- Password hashing using `werkzeug.security`

### **Authorization**
- Role checks via decorators:
- `@login_required`
- `@role_required("admin")`

### **Data security**
- Users (future) will only see:
- orders belonging to their company (company_id)
- restricted views based on role

---

# 7. Known Limitations & Future Architecture

### **Current Limitations**
- Monolithic architecture (sufficient for internal MVP)
- SQLite only (not scalable)
- No REST API
- Templates + JS mix can become harder to maintain long term

### **Future Architecture Plan**
- Add Flask Blueprint API (`/api/v1/...`)
- Move frontend to a React SPA
- Use PostgreSQL database
- Add Celery (optional) for notifications, scheduled tasks
- Convert to multi-tenant SaaS

---

# 8. Summary

FlowLogix is a clean, modular, Flask-based system structured for real-world
logistics operations and expandable into a SaaS platform. The architecture is
simple, maintainable, and intentionally built to evolve from:

**Internal dashboard → modern web app → micro-SaaS solution.**
