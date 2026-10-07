import json
import logging
import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from io import BytesIO
from pathlib import Path

from flask import Flask, current_app, flash, jsonify, redirect, render_template, request, send_file, url_for


class LibraryDatabase:
    def __init__(self, database_path=None):
        self.database_path = (
            Path(database_path)
            if database_path is not None
            else Path(__file__).resolve().with_name("library.db")
        )
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    author TEXT,
                    quantity INTEGER
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id INTEGER NOT NULL,
                    book_name TEXT NOT NULL,
                    author TEXT NOT NULL,
                    borrower TEXT NOT NULL,
                    issued_at TEXT NOT NULL,
                    returned_at TEXT
                )
                """
            )
            transaction_columns = {
                column[1]
                for column in connection.execute(
                    "PRAGMA table_info(transactions)"
                ).fetchall()
            }
            for column, definition in (
                ("student_name", "TEXT"),
                ("course", "TEXT"),
                ("due_date", "TEXT"),
            ):
                if column not in transaction_columns:
                    connection.execute(
                        f"ALTER TABLE transactions ADD COLUMN {column} {definition}"
                    )
            connection.execute(
                """
                UPDATE transactions
                SET student_name = borrower
                WHERE student_name IS NULL OR student_name = ''
                """
            )

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.database_path, timeout=10)
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def list_books(self):
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, name, author, quantity FROM books ORDER BY id"
            ).fetchall()
        return [
            {"id": row[0], "name": row[1], "author": row[2], "quantity": row[3]}
            for row in rows
        ]

    def list_issued_books(self):
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, book_name,
                       COALESCE(NULLIF(student_name, ''), borrower),
                       COALESCE(course, ''), issued_at, due_date
                FROM transactions
                WHERE returned_at IS NULL
                ORDER BY id DESC
                """
            ).fetchall()
        return [
            {
                "id": row[0],
                "book_name": row[1],
                "student_name": row[2],
                "course": row[3],
                "issued_at": row[4],
                "due_date": row[5],
            }
            for row in rows
        ]

    def add_book(self, name, author, quantity):
        if not name.strip() or not author.strip():
            raise ValueError("Enter a book name and author")
        if quantity <= 0:
            raise ValueError("Quantity must be a positive whole number")
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO books (name, author, quantity) VALUES (?, ?, ?)",
                (name.strip(), author.strip(), quantity),
            )

    def delete_book(self, book_id):
        with self._connect() as connection:
            active_issue = connection.execute(
                """
                SELECT 1 FROM transactions
                WHERE book_id = ? AND returned_at IS NULL
                LIMIT 1
                """,
                (book_id,),
            ).fetchone()
            if active_issue:
                raise ValueError("Return this book before deleting it")
            deleted = connection.execute(
                "DELETE FROM books WHERE id = ?", (book_id,)
            )
            if deleted.rowcount != 1:
                raise ValueError("The selected book no longer exists")

    def issue_book(self, book_id, student_name, course, due_date):
        if not student_name.strip() or not course.strip():
            raise ValueError("Enter the student's name and course")
        try:
            parsed_due_date = date.fromisoformat(due_date)
        except ValueError as error:
            raise ValueError("Enter the due date as YYYY-MM-DD") from error
        if parsed_due_date.isoformat() != due_date:
            raise ValueError("Enter the due date as YYYY-MM-DD")
        if parsed_due_date < date.today():
            raise ValueError("The due date cannot be in the past")

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            book = connection.execute(
                "SELECT name, author FROM books WHERE id = ?", (book_id,)
            ).fetchone()
            if book is None:
                raise ValueError("The selected book no longer exists")

            updated = connection.execute(
                "UPDATE books SET quantity = quantity - 1 "
                "WHERE id = ? AND quantity > 0",
                (book_id,),
            )
            if updated.rowcount != 1:
                raise ValueError("No copies of this book are currently available")

            connection.execute(
                """
                INSERT INTO transactions
                    (book_id, book_name, author, borrower, student_name,
                     course, due_date, issued_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    book_id,
                    book[0],
                    book[1],
                    student_name.strip(),
                    student_name.strip(),
                    course.strip(),
                    due_date,
                    self._now(),
                ),
            )

    def return_book(self, transaction_id):
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            transaction = connection.execute(
                """
                SELECT book_id, returned_at
                FROM transactions
                WHERE id = ?
                """,
                (transaction_id,),
            ).fetchone()
            if transaction is None:
                raise ValueError("The selected transaction no longer exists")
            if transaction[1] is not None:
                raise ValueError("This book has already been returned")

            updated = connection.execute(
                "UPDATE books SET quantity = quantity + 1 WHERE id = ?",
                (transaction[0],),
            )
            if updated.rowcount != 1:
                raise ValueError("The book is no longer in the inventory")

            connection.execute(
                "UPDATE transactions SET returned_at = ? WHERE id = ?",
                (self._now(), transaction_id),
            )

    @staticmethod
    def _now():
        return datetime.now().astimezone().isoformat(timespec="seconds")


def create_app(database_path=None):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get(
        "LIBRARY_SECRET_KEY", "development-key-change-before-deployment"
    )
    app.config["DATABASE"] = (
        Path(database_path)
        if database_path is not None
        else Path(__file__).resolve().with_name("library.db")
    )
    database = LibraryDatabase(app.config["DATABASE"])
    app.extensions["library_database"] = database

    @app.get("/")
    def index():
        page = request.args.get("page", "home")
        if page not in {"home", "add", "issue", "issued"}:
            page = "home"
        books = database.list_books()
        issued_books = database.list_issued_books()
        return render_template(
            "index.html",
            page=page,
            books=books,
            available_books=[book for book in books if book["quantity"] > 0],
            issued_books=issued_books,
            today=date.today().isoformat(),
        )

    @app.post("/books")
    def add_book():
        name = request.form.get("name", "").strip()
        author = request.form.get("author", "").strip()
        quantity_text = request.form.get("quantity", "").strip()
        try:
            quantity = int(quantity_text)
        except ValueError:
            flash("Quantity must be a positive whole number.", "error")
            return redirect(url_for("index", page="add"))

        try:
            database.add_book(name, author, quantity)
        except ValueError as error:
            flash(str(error), "error")
            return redirect(url_for("index", page="add"))
        except sqlite3.Error:
            _report_database_error()
            flash("The book could not be saved because of a database error.", "error")
            return redirect(url_for("index", page="add"))

        flash("Book added successfully.", "success")
        return redirect(url_for("index", page="add"))

    @app.post("/books/<int:book_id>/delete")
    def delete_book(book_id):
        try:
            database.delete_book(book_id)
        except ValueError as error:
            flash(str(error), "error")
        except sqlite3.Error:
            _report_database_error()
            flash("The book could not be deleted because of a database error.", "error")
        else:
            flash("Book deleted successfully.", "success")
        return redirect(url_for("index", page="add"))

    @app.post("/books/issue")
    def issue_book():
        book_id_text = request.form.get("book_id", "")
        if not book_id_text.isdecimal():
            flash("Select a valid book to issue.", "error")
            return redirect(url_for("index", page="issue"))
        try:
            book_id = int(book_id_text)
            database.issue_book(
                book_id,
                request.form.get("student_name", ""),
                request.form.get("course", ""),
                request.form.get("due_date", ""),
            )
        except ValueError as error:
            flash(str(error), "error")
        except sqlite3.Error:
            _report_database_error()
            flash("The book could not be issued because of a database error.", "error")
        else:
            flash("Book issued successfully.", "success")
        return redirect(url_for("index", page="issue"))

    @app.post("/transactions/<int:transaction_id>/return")
    def return_book(transaction_id):
        try:
            database.return_book(transaction_id)
        except ValueError as error:
            flash(str(error), "error")
        except sqlite3.Error:
            _report_database_error()
            flash("The book could not be returned because of a database error.", "error")
        else:
            flash("Book returned successfully.", "success")
        return redirect(url_for("index", page="issued"))

    @app.get("/api/books")
    def books_api():
        try:
            return jsonify(books=database.list_books())
        except sqlite3.Error:
            _report_database_error()
            return jsonify(error="The book list is temporarily unavailable."), 500

    @app.get("/books/export")
    def export_books():
        try:
            export_data = json.dumps(
                {"books": database.list_books()},
                ensure_ascii=False,
                indent=2,
            ).encode("utf-8")
        except sqlite3.Error:
            _report_database_error()
            flash("Books could not be exported because of a database error.", "error")
            return redirect(url_for("index", page="add"))
        return send_file(
            BytesIO(export_data),
            mimetype="application/json",
            as_attachment=True,
            download_name="library-books.json",
        )

    return app


def _report_database_error():
    current_app.logger.exception("Library database operation failed")


def main():
    logging.basicConfig(level=logging.INFO)
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=False)


if __name__ == "__main__":
    main()
