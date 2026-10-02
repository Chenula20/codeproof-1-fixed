import unittest
from pathlib import Path
from src.auth.handler import validate_login
from src.api.events import upcoming_events


class AuthenticationTests(unittest.TestCase):
    def test_valid_credentials(self):
        self.assertEqual(validate_login({"username": "student", "password": "example-only"})[1], 200)

    def test_invalid_credentials(self):
        self.assertEqual(validate_login({"username": "student", "password": "wrong"})[1], 401)

    def test_missing_credentials(self):
        self.assertEqual(validate_login({"email": "student", "password": "example-only"})[1], 422)

    def test_frontend_contract(self):
        source = Path("src/frontend/login.js").read_text()
        self.assertIn("{ username: username, password }", source)

    def test_events_regression(self):
        self.assertEqual(upcoming_events([{"date": "2026-01-01"}], "2026-09-01"), [])
