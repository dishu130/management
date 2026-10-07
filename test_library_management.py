import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from library_management import LibraryDatabase, create_app


class LibraryDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database = LibraryDatabase(
            Path(self.temp_directory.name) / "test-library.db"
        )

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_issue_and_return_update_available_quantity(self):
        self.database.add_book("A Study in Scarlet", "Arthur Conan Doyle", 1)
        book_id = self.database.list_books()[0]["id"]
        due_date = (date.today() + timedelta(days=7)).isoformat()

        self.database.issue_book(book_id, "Alex Reader", "Literature", due_date)

        self.assertEqual(self.database.list_books()[0]["quantity"], 0)
        loan = self.database.list_issued_books()[0]
        self.assertEqual(loan["student_name"], "Alex Reader")
        with self.assertRaisesRegex(ValueError, "No copies"):
            self.database.issue_book(book_id, "Another Reader", "History", due_date)

        self.database.return_book(loan["id"])

        self.assertEqual(self.database.list_books()[0]["quantity"], 1)
        self.assertEqual(self.database.list_issued_books(), [])

    def test_cannot_delete_a_book_with_an_active_loan(self):
        self.database.add_book("A Study in Scarlet", "Arthur Conan Doyle", 1)
        book_id = self.database.list_books()[0]["id"]
        due_date = (date.today() + timedelta(days=7)).isoformat()
        self.database.issue_book(book_id, "Alex Reader", "Literature", due_date)

        with self.assertRaisesRegex(ValueError, "Return this book"):
            self.database.delete_book(book_id)


class LibraryWebAppTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.app = create_app(Path(self.temp_directory.name) / "test-library.db")
        self.app.config.update(TESTING=True, SECRET_KEY="test-key")
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_inventory_page_add_and_json_export(self):
        response = self.client.post(
            "/books",
            data={"name": "A Study in Scarlet", "author": "Arthur Conan Doyle", "quantity": "2"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request.args.get("page"), "add")
        self.assertIn(b"<h2>Add or Manage Books</h2>", response.data)
        self.assertIn(b"A Study in Scarlet", response.data)

        inventory_response = self.client.get("/?page=add")
        self.assertIn(b"A Study in Scarlet", inventory_response.data)

        api_response = self.client.get("/api/books")
        self.assertEqual(api_response.status_code, 200)
        self.assertEqual(api_response.json["books"][0]["quantity"], 2)

        export_response = self.client.get("/books/export")
        self.assertEqual(export_response.status_code, 200)
        self.assertEqual(export_response.mimetype, "application/json")
        self.assertEqual(
            json.loads(export_response.data)["books"][0]["name"],
            "A Study in Scarlet",
        )

    def test_form_rejects_non_integer_quantity(self):
        response = self.client.post(
            "/books",
            data={"name": "A Study in Scarlet", "author": "Arthur Conan Doyle", "quantity": "many"},
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request.args.get("page"), "add")
        self.assertIn(b"<h2>Add or Manage Books</h2>", response.data)
        self.assertIn(b"positive whole number", response.data)
        self.assertEqual(self.client.get("/api/books").json["books"], [])

    def test_web_issue_return_and_delete_flow(self):
        self.client.post(
            "/books",
            data={"name": "A Study in Scarlet", "author": "Arthur Conan Doyle", "quantity": "1"},
        )
        book_id = self.client.get("/api/books").json["books"][0]["id"]
        due_date = (date.today() + timedelta(days=7)).isoformat()

        issue_response = self.client.post(
            "/books/issue",
            data={
                "book_id": str(book_id),
                "student_name": "Alex Reader",
                "course": "Literature",
                "due_date": due_date,
            },
            follow_redirects=True,
        )
        self.assertEqual(issue_response.status_code, 200)
        self.assertEqual(issue_response.request.args.get("page"), "issue")
        self.assertIn(b"<h2>Issue a Book</h2>", issue_response.data)
        self.assertIn(b"Book issued successfully", issue_response.data)
        self.assertEqual(self.client.get("/api/books").json["books"][0]["quantity"], 0)

        loan_id = self.app.extensions["library_database"].list_issued_books()[0]["id"]
        return_response = self.client.post(
            f"/transactions/{loan_id}/return",
            follow_redirects=True,
        )
        self.assertEqual(return_response.status_code, 200)
        self.assertEqual(return_response.request.args.get("page"), "issued")
        self.assertIn(b"<h2>Issued Books</h2>", return_response.data)
        self.assertIn(b"Book returned successfully", return_response.data)
        self.assertEqual(self.client.get("/api/books").json["books"][0]["quantity"], 1)

        delete_response = self.client.post(
            f"/books/{book_id}/delete",
            follow_redirects=True,
        )
        self.assertEqual(delete_response.status_code, 200)
        self.assertEqual(delete_response.request.args.get("page"), "add")
        self.assertIn(b"<h2>Add or Manage Books</h2>", delete_response.data)
        self.assertEqual(self.client.get("/api/books").json["books"], [])

    def test_route_redirects_and_not_found_handling(self):
        # Direct routes should redirect properly without 404
        for path, expected_page in [
            ("/home", "home"),
            ("/add", "add"),
            ("/books", "add"),
            ("/issue", "issue"),
            ("/issued", "issued"),
        ]:
            resp = self.client.get(path, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.request.args.get("page"), expected_page)

        # Invalid URL should be redirected to home with flash message
        invalid_resp = self.client.get("/nonexistent-page", follow_redirects=True)
        self.assertEqual(invalid_resp.status_code, 200)
        self.assertIn(b"The requested page was not found", invalid_resp.data)


if __name__ == "__main__":
    unittest.main()
