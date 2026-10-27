import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app import create_app  # noqa: E402


class ExpenseApiTests(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.client = create_app({"DATABASE": self.path, "TESTING": True}).test_client()

    def tearDown(self):
        os.remove(self.path)

    def add(self, **kw):
        body = {"type": "expense", "amount": 10, "category": "Food", "date": "2026-10-01"}
        body.update(kw)
        return self.client.post("/api/transactions", json=body)

    def test_create_and_get(self):
        r = self.add(description="Lunch")
        self.assertEqual(r.status_code, 201)
        data = r.get_json()
        self.assertEqual(data["category"], "food")
        r = self.client.get(f"/api/transactions/{data['id']}")
        self.assertEqual(r.get_json()["description"], "Lunch")

    def test_validation_errors(self):
        self.assertEqual(self.add(amount=-5).status_code, 400)
        self.assertEqual(self.add(type="gift").status_code, 400)
        self.assertEqual(self.add(date="01-10-2026").status_code, 400)
        r = self.client.post("/api/transactions", json={})
        self.assertEqual(r.status_code, 400)
        r = self.client.post("/api/transactions", data="not json", content_type="text/plain")
        self.assertEqual(r.status_code, 400)

    def test_update_and_delete(self):
        tid = self.add().get_json()["id"]
        r = self.client.put(f"/api/transactions/{tid}", json={"amount": 25.5})
        self.assertEqual(r.get_json()["amount"], 25.5)
        self.assertEqual(self.client.put(f"/api/transactions/{tid}", json={}).status_code, 400)
        self.assertEqual(self.client.delete(f"/api/transactions/{tid}").status_code, 200)
        self.assertEqual(self.client.get(f"/api/transactions/{tid}").status_code, 404)
        self.assertEqual(self.client.delete(f"/api/transactions/{tid}").status_code, 404)

    def test_filters_and_summary(self):
        self.add(type="income", amount=1000, category="salary", date="2026-10-01")
        self.add(amount=100, category="food", date="2026-10-05")
        self.add(amount=50, category="travel", date="2026-11-02")
        r = self.client.get("/api/transactions?category=food")
        self.assertEqual(r.get_json()["count"], 1)
        r = self.client.get("/api/transactions?start_date=2026-10-01&end_date=2026-10-31")
        self.assertEqual(r.get_json()["count"], 2)
        r = self.client.get("/api/transactions?type=income")
        self.assertEqual(r.get_json()["count"], 1)
        s = self.client.get("/api/summary").get_json()
        self.assertEqual(s["total_income"], 1000)
        self.assertEqual(s["total_expenses"], 150)
        self.assertEqual(s["balance"], 850)
        s = self.client.get("/api/summary?end_date=2026-10-31").get_json()
        self.assertEqual(s["balance"], 900)
        self.assertEqual(self.client.get("/api/transactions?start_date=bad").status_code, 400)

    def test_home_page_and_api_index(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Expense Tracker", r.data)
        r.close()
        self.assertIn("endpoints", self.client.get("/api").get_json())

    def test_categories(self):
        self.add(category="Food")
        self.add(category="Rent")
        self.assertEqual(self.client.get("/api/categories").get_json()["categories"], ["food", "rent"])


if __name__ == "__main__":
    unittest.main()
