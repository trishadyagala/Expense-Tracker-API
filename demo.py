"""Runs the whole API in one window: no server, no second terminal needed.
Usage:  python demo.py
Uses a temporary database, so it never touches expenses.db.
"""
import json
import os
import tempfile

from app import create_app

fd, path = tempfile.mkstemp(suffix=".db")
os.close(fd)
client = create_app({"DATABASE": path, "TESTING": True}).test_client()


def show(title, response):
    print(f"\n=== {title} -> {response.status_code}")
    print(json.dumps(response.get_json(), indent=2))


show("Add income", client.post("/api/transactions", json={"type": "income", "amount": 50000, "category": "salary", "date": "2026-10-01"}))
show("Add expense", client.post("/api/transactions", json={"type": "expense", "amount": 250, "category": "food", "description": "Groceries", "date": "2026-10-05"}))
show("Add expense", client.post("/api/transactions", json={"type": "expense", "amount": 1200, "category": "travel", "date": "2026-11-02"}))
show("List all", client.get("/api/transactions"))
show("Filter: category=food", client.get("/api/transactions?category=food"))
show("Filter: October only", client.get("/api/transactions?start_date=2026-10-01&end_date=2026-10-31"))
show("Update #2 amount to 300", client.put("/api/transactions/2", json={"amount": 300}))
show("Delete #3", client.delete("/api/transactions/3"))
show("Summary", client.get("/api/summary"))
show("Validation error (expect 400)", client.post("/api/transactions", json={"type": "expense", "amount": -5, "category": "food"}))

os.remove(path)
print("\nDone. Everything above ran without starting a server.")
