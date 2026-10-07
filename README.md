# Campus Library Management

A small browser-based library manager built with Python, Flask, HTML, CSS, SQLite, and JSON.

## Run locally

1. Create and activate a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Start the app with `python library_management.py`.
4. Open `http://127.0.0.1:5000` in your browser.

The app creates `library.db` beside `library_management.py` on its first run. If you are deploying beyond a local development machine, set the `LIBRARY_SECRET_KEY` environment variable to a unique secret key.

## Features

- Add, view, and delete books in the SQLite inventory.
- Issue available copies to students and record courses and due dates.
- Return books and update available-copy counts.
- Read the inventory as JSON at `/api/books` or download it from **Export JSON**.

## Python concepts in use

- **Variables, data types, operators, and conditionals:** validating form input, calculating available inventory, and checking due dates.
- **Lists and dictionaries:** representing query results for templates and JSON responses.
- **Functions, classes, and objects:** Flask route functions and the `LibraryDatabase` class.
- **File handling and JSON:** the export route serializes inventory into a JSON file download using an in-memory file object.
- **Exception handling:** invalid input is reported to the user, and database failures are logged and surfaced as an error message.
- **Database connectivity:** SQLite connections use parameterized queries and transaction handling.
# collegelibrary
# lib
# libb
# libmgt
