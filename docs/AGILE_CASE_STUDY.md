# FlowLogix – Agile Case Study

FlowLogix is a real-world internal project developed using Agile principles.
This document explains how the project was managed, structured, iterated, and
delivered using a lightweight Scrum/Kanban hybrid.

The goal is to demonstrate a clear understanding of **Agile delivery**,  
**product thinking**, and **full-stack execution**.

---

# 1. Product Vision

FlowLogix is a lightweight supply-chain dashboard built for a pharmaceutical
logistics workflow. Its purpose is to:

- centralize all shipment information in one place,
- visualize ETD / ETA / ATA timelines,
- identify delays and bottlenecks early,
- simplify warehouse + delivery operations,
- reduce dependency on Excel spreadsheets and email updates.

The system is designed as an **MVP**, with a clear path toward becoming
a multi-user logistics productivity tool and eventually a micro-SaaS.

---

# 2. Stakeholders & Roles

Although this is a small project, the roles were explicitly defined:

| Role | Responsibilities |
|------|------------------|
| **Stakeholder / Product Owner** | Defines business needs, prioritizes features |
| **Project Manager / Scrum Facilitator** | Organizes work, creates backlog, runs sprints, ensures transparency |
| **Full-Stack Developer** | Implements backend + frontend features, fixes bugs, handles deployment |

In this project, I fulfilled **all** of the above roles (common in MVP development).

---

# 3. Agile Approach

FlowLogix follows a **Scrum-inspired Agile workflow**:

- Work is divided into **Sprints** (1 week each).
- Features are managed as **User Stories**.
- Bugs and tech debt are tracked in the **Backlog**.
- Each Sprint has:
  - a **goal**,  
  - a **committed scope**,  
  - a **demoable increment**,  
  - and **retro notes**.

The goal is to maintain a continuous flow while keeping work small and vertical.

---

# 4. Backlog Structure

Backlog items were categorized as:

### **User Stories**
Format:

> *As a* **[role]**,  
> *I want* **[feature]**,  
> *so that* **[benefit]**.

Examples:

- *As a logistics manager, I want to see all orders on a timeline so that I can detect delays immediately.*
- *As a warehouse operator, I want a separate Warehouse view so I can update stock without overwhelming the main dashboard.*
- *As an admin, I want to assign roles so users only see their own company’s orders.*

### **Bugs**
- UI or logic inconsistencies  
- Incorrect ETA validation  
- Sorting/filtering mismatches between table and timeline

### **Technical Tasks**
- File clean-up
- Route refactors
- Consistent modal logic
- Improving dark mode

### **Enhancements**
- Better UX in modals
- More accurate filtering
- Analytics and reports

Each item was assigned to a Sprint or placed in the long-term roadmap.

---

# 5. Sprint Structure

Work was executed across several short Sprints.

Full Sprint notes live in `docs/SPRINTS/`.

Below is a summary of the first four Sprints.

---

## **Sprint 1 – Core Dashboard (Vertical Slice)**

**Goal:** Build the smallest usable version of the dashboard.

**Delivered:**
- Flask project setup
- User / Order models
- Dashboard table + Chart.js timeline
- Basic filtering and data seeding

**Outcome:**  
Internal users could see their shipments visually for the first time.

---

## **Sprint 2 – Warehouse & Delivered Views**

**Goal:** Support the full shipment lifecycle.

**Delivered:**
- Warehouse tab
- Delivered tab
- Consistent table interactions
- Status transitions (In Process → Warehouse → Delivered)

**Outcome:**  
Clear separation between transit, warehouse, and completed orders.

---

## **Sprint 3 – Stockreport + UX Consistency**

**Goal:** Add deeper cargo tracking and refine the UI.

**Delivered:**
- First version of Stockreport (Arrived / Stocked / Delivered)
- Modals for editing orders and stock movements
- Improved dark mode, validation, navbar, layout

**Outcome:**  
Reduced confusion and improved accuracy in warehouse data entry.

---

## **Sprint 4 – Refactoring & Demo Preparation**

**Goal:** Stabilize the app and prepare it as a portfolio-quality project.

**Delivered:**
- Clean repo structure
- Modular route logic
- Unified table actions
- Documentation folder
- Architecture, Roadmap, Agile Case Study
- Demo-friendly dataset

**Outcome:**  
Project is now clean, demonstrable, and maintainable.

---

# 6. Tools & Workflow

### **Version Control**
- GitHub repository with structured commits
- Feature branches during implementation
- Clean commit messages (chore, fix, docs, feature)

### **Documentation**
- Architecture (`ARCHITECTURE.md`)
- Roadmap (`ROADMAP.md`)
- Sprint summaries (`SPRINTS/`)
- This Agile case study

### **DevOps**
- Deployment using Render (Gunicorn + WSGI)
- Auto-restart on changes

### **Project Board**
(Planned for next step)
- Backlog
- Selected for Sprint
- In Progress
- In Review
- Done

---

# 7. Continuous Improvement

Throughout development several positive practices emerged:

- Early prototypes helped validate requirements.  
- Keeping each Sprint small prevented overwhelm.  
- Writing Sprint notes improved clarity and decision-mak
