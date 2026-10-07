# Library Management System

A Python and Flask-based web application for managing library books, tracking student book issues, and handling returns with SQLite database integration and JSON data handling.

Developed as a **Python Programming Mini-Project** in accordance with academic project guidelines.

---

## 1. Problem Statement & Objectives

### Problem Statement
Managing a library manually using physical logbooks or spreadsheets often leads to inventory discrepancies, lost books, unrecorded dues, and inefficient record retrieval.

### Objectives
- Provide a centralized system to add, view, and delete books in the library inventory.
- Track book issuance to students with course details and scheduled return dates.
- Prevent over-issuing by automatically validating available stock before issuing.
- Manage return transactions and immediately restore book quantities in real time.
- Offer data export functionality in JSON format for external records and interoperability.

---

## 2. Key Modules & Features

The project implements full **CRUD (Create, Read, Update, Delete)** operations:

- **Book Inventory Management (Create, Read, Delete)**:
  - Add new books with title, author, and available copy count.
  - View current stock and available quantity.
  - Delete books from inventory (safely protected against deleting books currently on loan).
- **Issue Management (Create, Update)**:
  - Issue available books to students with student name, course, and return due date.
  - Automatically checks that copies are in stock before granting a loan.
  - Decrements available quantity upon issue.
- **Return Tracking (Update)**:
  - View all currently issued books with loan metadata and due dates.
  - Return books with a single click, recording return timestamp and restoring inventory stock.
- **Data Export & API (Data Handling)**:
  - RESTful JSON API endpoint (`/api/books`) for querying library inventory.
  - Downloadable JSON export (`/books/export`) for offline backup and data interchange.

---

## 3. Technologies Used

- **Core Programming Language**: Python 3
- **Web Framework**: Flask
- **Database**: SQLite3 (relational database with ACID transactions)
- **Frontend / UI**: HTML5, Vanilla CSS3
- **Data Interchange**: JSON

---

## 4. Python Concepts Demonstrated

As required by the course curriculum, the application demonstrates:

- **Object-Oriented Programming (OOP)**:
  - `LibraryDatabase` class encapsulates database schema setup, queries, and business logic.
- **Database Connectivity & Transaction Management**:
  - Python `sqlite3` module with parameterized queries to prevent SQL injection.
  - Python `@contextmanager` generator pattern for safe transaction commit/rollback and connection closing.
- **Input Validation & Exception Handling**:
  - Validates positive integers for book quantities, required fields, and valid date formats.
  - Graceful handling of database errors with logging and user-friendly flash notifications.
- **File & Stream Handling**:
  - In-memory binary streams (`io.BytesIO`) and JSON serialization (`json.dumps`) to generate downloadable export files without creating temporary clutter on disk.
- **Data Structures**:
  - Lists of dictionaries for query results, sets for schema introspection, and tuples for parameterized queries.
- **Automated Testing**:
  - Built-in `unittest` test suite verifying database methods, edge cases, and HTTP endpoints.

---

## 5. Project Directory Structure

```text
library/
├── api/
│   └── index.py                 # Serverless function entrypoint (Vercel)
├── templates/
│   └── index.html               # Web interface template
├── static/
│   └── style.css                # Custom styling for UI
├── library_management.py        # Main Python application (Flask routes & database logic)
├── test_library_management.py   # Automated unit and integration test suite
├── requirements.txt             # Project dependencies (Flask, Gunicorn)
├── library.db                   # SQLite database file (created automatically)
├── Procfile                     # Production process configuration (Render)
├── vercel.json                  # Cloud routing & bundle configuration (Vercel)
├── .gitignore                   # Standard Git ignore file for Python
└── README.md                    # Project documentation
```

---

## 6. How to Run Locally

### Prerequisites
- Python 3.8 or higher installed on your system.

### Step 1: Clone or Navigate to the Project
```bash
cd library
```

### Step 2: (Optional) Create and Activate a Virtual Environment
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run the Application
```bash
python library_management.py
```

### Step 5: Open in Your Browser
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

> **Note:** The SQLite database `library.db` is initialized automatically on first run if it does not already exist.

---

## 7. Cloud Deployment Guide

The project is pre-configured for instant zero-configuration deployment on leading cloud hosting platforms:

### Deploying to Vercel
1. Push the repository to GitHub.
2. Go to [Vercel](https://vercel.com) and click **Add New Project** -> **Import Git Repository**.
3. Keep default settings and click **Deploy**.
4. Vercel automatically detects `vercel.json` and `api/index.py`, bundle templates and styles, and routes all traffic to the Flask application without any 404 or path resolution errors.

### Deploying to Render
1. Go to [Render Dashboard](https://dashboard.render.com) and create a new **Web Service**.
2. Connect your GitHub repository.
3. Render automatically picks up `requirements.txt` and `Procfile` (`web: gunicorn library_management:app`).
4. Click **Create Web Service**.

---

## 8. Running the Test Suite

Execute the unit tests using Python's built-in `unittest` module:
```bash
python -m unittest test_library_management.py
```

---

## 9. Group Members & Contributions

| Member Name | Role / Contribution |
|-------------|---------------------|
| *Member 1*  | Database schema design, `LibraryDatabase` class & CRUD operations |
| *Member 2*  | Flask routes, business logic, issue/return workflows & input validation |
| *Member 3*  | Frontend interface (HTML/CSS), JSON export feature & testing |
