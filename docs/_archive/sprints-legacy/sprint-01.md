# Sprint 1 – Core Dashboard (Vertical Slice)
**Duration:** 1 week  
**Sprint Goal:** Deliver the smallest usable version of the supply tracking dashboard, including database setup, order model, and basic UI visualization.

---

## 🎯 Objectives
- Establish Flask project structure and configuration
- Implement User and Order models
- Set up the initial SQLite database and migrations
- Build a basic dashboard with a table of orders
- Add the first version of the Chart.js timeline (ETD → ETA)

---

## ✅ Completed Work
- Flask project scaffolded with app factory pattern
- SQLAlchemy configured with `Order` and `User` models
- Basic seed data for initial testing (`seed_boot.py`)
- Table view implemented in `dashboard.html`
- First Chart.js horizontal timeline using ETD and ETA
- Basic filtering and sorting logic

---

## ❗ Not Completed / Moved to Next Sprint
- Role-based access control
- Warehouse and Delivered lifecycle pages
- Refined UI and UX improvements

---

## 🔎 Demo Summary
Users can now:
- Authenticate via login page  
- View all orders in a sortable table  
- See timeline visualization for shipping progress  

This delivered the **first working vertical slice**.

---

## 🔄 Retrospective
**What went well**
- Early vertical slice helped validate data model and visualization approach  
- Quick feedback allowed adjustment before expanding complexity  

**What to improve**
- Split features into even smaller tasks  
<<<<<<< HEAD
- Add more realistic demo data for testing timeline logic
=======
- Add more realistic demo data for testing timeline logic
>>>>>>> 984c2f7d744f643c8ad9ecca702b4c040353cc5d
