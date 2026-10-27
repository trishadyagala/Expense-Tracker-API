# REST API Expense Tracker

A beginner-friendly REST API for tracking income and expenses, built with **Flask** and **SQLite** (raw SQL, no ORM).

## Features
- Add income and expense transactions
- Categorize transactions
- Update and delete transactions
- Filter by type, category, and date range
- Totals: income, expenses, and balance (with per-category breakdown)
- Simple web page (served at `/`) to add, edit, delete, filter transactions and see totals
- Input validation and consistent JSON error responses
- Unit tests and a ready-to-import Postman collection

## Tech stack
Python 3.9+, Flask, SQLite (`sqlite3` from the standard library)

## Getting started

```bash
git clone https://github.com/trishadyagala/expense-tracker-api.git
cd expense-tracker-api

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python app.py                    # http://127.0.0.1:5000
```

Open http://127.0.0.1:5000 for the web page. The JSON API lives under `/api`.
The database file (`expenses.db`) is created automatically on first run.
Set the `DATABASE` environment variable to use a different path.

## API endpoints

| Method | Endpoint                  | Purpose                                   |
|--------|---------------------------|-------------------------------------------|
| GET    | `/api/transactions`       | List transactions (supports filters)      |
| GET    | `/api/transactions/<id>`  | Get one transaction                       |
| POST   | `/api/transactions`       | Add a transaction                         |
| PUT    | `/api/transactions/<id>`  | Update a transaction (partial allowed)    |
| DELETE | `/api/transactions/<id>`  | Delete a transaction                      |
| GET    | `/api/summary`            | Total income, expenses, balance           |
| GET    | `/api/categories`         | List all categories in use                |

### Transaction fields
| Field         | Type   | Notes                                     |
|---------------|--------|-------------------------------------------|
| `type`        | string | `income` or `expense` (required)          |
| `amount`      | number | Positive number (required)                |
| `category`    | string | 1-50 chars, stored lowercase (required)   |
| `description` | string | Optional, up to 255 chars                 |
| `date`        | string | `YYYY-MM-DD`, defaults to today           |

### Filters (for `/api/transactions` and `/api/summary`)
`type`, `category`, `start_date`, `end_date`

```
GET /api/transactions?category=food&start_date=2026-10-01&end_date=2026-10-31
GET /api/summary?type=expense
```

## Examples

```bash
# Add an expense
curl -X POST http://127.0.0.1:5000/api/transactions \
  -H "Content-Type: application/json" \
  -d '{"type":"expense","amount":250.50,"category":"Food","description":"Groceries","date":"2026-10-28"}'

# Add income
curl -X POST http://127.0.0.1:5000/api/transactions \
  -H "Content-Type: application/json" \
  -d '{"type":"income","amount":50000,"category":"Salary"}'

# Update
curl -X PUT http://127.0.0.1:5000/api/transactions/1 \
  -H "Content-Type: application/json" -d '{"amount": 300}'

# Summary
curl http://127.0.0.1:5000/api/summary
```

Sample summary response:
```json
{
  "total_income": 50000.0,
  "total_expenses": 300.0,
  "balance": 49700.0,
  "transaction_count": 2,
  "by_category": [
    {"category": "salary", "type": "income", "total": 50000.0},
    {"category": "food", "type": "expense", "total": 300.0}
  ]
}
```

## Status codes
`200` OK · `201` Created · `400` Validation error · `404` Not found · `405` Method not allowed · `500` Server error

Errors look like:
```json
{"error": "Validation failed.", "details": {"amount": "Must be a positive number."}}
```

## Testing

```bash
python -m unittest discover -s tests -v
```

For manual testing, import `postman/expense_tracker.postman_collection.json` into Postman.

## Project structure
```
expense-tracker-api/
├── app.py          # Flask app, routes, error handlers
├── db.py           # SQLite connection + schema
├── static/index.html  # Web page frontend
├── validators.py   # Input validation
├── tests/          # Unit tests
├── postman/        # Postman collection
└── requirements.txt
```

## Possible improvements
- Pagination and sorting
- Monthly spending chart (Chart.js or matplotlib)
- User accounts with JWT authentication
- Switch to MySQL/PostgreSQL with SQLAlchemy
- Docker support
