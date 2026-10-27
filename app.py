"""REST API based Expense Tracker (Flask + SQLite)."""
import os
import sqlite3

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException

import db
from validators import validate_filters, validate_transaction


def create_app(config=None):
    app = Flask(__name__)
    app.config["DATABASE"] = os.environ.get("DATABASE", "expenses.db")
    if config:
        app.config.update(config)
    db.init_app(app)

    # ---------- helpers ----------
    def row_to_dict(row):
        return {k: row[k] for k in row.keys()}

    def error(message, status, details=None):
        body = {"error": message}
        if details:
            body["details"] = details
        return jsonify(body), status

    def build_where(filters):
        clauses, params = [], []
        if "type" in filters:
            clauses.append("type = ?")
            params.append(filters["type"])
        if "category" in filters:
            clauses.append("category = ?")
            params.append(filters["category"])
        if "start_date" in filters:
            clauses.append("date >= ?")
            params.append(filters["start_date"])
        if "end_date" in filters:
            clauses.append("date <= ?")
            params.append(filters["end_date"])
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        return where, params

    def get_json_body():
        data = request.get_json(silent=True)
        return data

    # ---------- routes ----------
    @app.get("/")
    def home():
        return send_from_directory(app.static_folder, "index.html")

    @app.get("/api")
    def api_index():
        return jsonify({
            "name": "Expense Tracker API",
            "endpoints": [
                "GET    /api/transactions",
                "GET    /api/transactions/<id>",
                "POST   /api/transactions",
                "PUT    /api/transactions/<id>",
                "DELETE /api/transactions/<id>",
                "GET    /api/summary",
                "GET    /api/categories",
            ],
        })

    @app.get("/api/transactions")
    def list_transactions():
        filters, errors = validate_filters(request.args)
        if errors:
            return error("Invalid query parameters.", 400, errors)
        where, params = build_where(filters)
        rows = db.get_db().execute(
            f"SELECT * FROM transactions {where} ORDER BY date DESC, id DESC", params
        ).fetchall()
        return jsonify({"count": len(rows), "transactions": [row_to_dict(r) for r in rows]})

    @app.get("/api/transactions/<int:txn_id>")
    def get_transaction(txn_id):
        row = db.get_db().execute(
            "SELECT * FROM transactions WHERE id = ?", (txn_id,)
        ).fetchone()
        if row is None:
            return error(f"Transaction {txn_id} not found.", 404)
        return jsonify(row_to_dict(row))

    @app.post("/api/transactions")
    def create_transaction():
        clean, errors = validate_transaction(get_json_body())
        if errors:
            return error("Validation failed.", 400, errors)
        conn = db.get_db()
        cur = conn.execute(
            "INSERT INTO transactions (type, amount, category, description, date) "
            "VALUES (:type, :amount, :category, :description, :date)",
            {"description": "", **clean},
        )
        conn.commit()
        row = conn.execute("SELECT * FROM transactions WHERE id = ?", (cur.lastrowid,)).fetchone()
        response = jsonify(row_to_dict(row))
        response.status_code = 201
        response.headers["Location"] = f"/api/transactions/{cur.lastrowid}"
        return response

    @app.put("/api/transactions/<int:txn_id>")
    @app.patch("/api/transactions/<int:txn_id>")
    def update_transaction(txn_id):
        conn = db.get_db()
        if conn.execute("SELECT 1 FROM transactions WHERE id = ?", (txn_id,)).fetchone() is None:
            return error(f"Transaction {txn_id} not found.", 404)
        clean, errors = validate_transaction(get_json_body(), partial=True)
        if errors:
            return error("Validation failed.", 400, errors)
        # Column names come from the validator's fixed whitelist, never from user input.
        assignments = ", ".join(f"{col} = :{col}" for col in clean)
        conn.execute(f"UPDATE transactions SET {assignments} WHERE id = :id", {**clean, "id": txn_id})
        conn.commit()
        row = conn.execute("SELECT * FROM transactions WHERE id = ?", (txn_id,)).fetchone()
        return jsonify(row_to_dict(row))

    @app.delete("/api/transactions/<int:txn_id>")
    def delete_transaction(txn_id):
        conn = db.get_db()
        cur = conn.execute("DELETE FROM transactions WHERE id = ?", (txn_id,))
        conn.commit()
        if cur.rowcount == 0:
            return error(f"Transaction {txn_id} not found.", 404)
        return jsonify({"message": f"Transaction {txn_id} deleted."})

    @app.get("/api/summary")
    def summary():
        filters, errors = validate_filters(request.args)
        if errors:
            return error("Invalid query parameters.", 400, errors)
        where, params = build_where(filters)
        conn = db.get_db()
        totals = conn.execute(
            "SELECT "
            "COALESCE(SUM(CASE WHEN type='income'  THEN amount END), 0) AS total_income, "
            "COALESCE(SUM(CASE WHEN type='expense' THEN amount END), 0) AS total_expenses, "
            f"COUNT(*) AS transaction_count FROM transactions {where}",
            params,
        ).fetchone()
        by_category = conn.execute(
            f"SELECT category, type, ROUND(SUM(amount), 2) AS total FROM transactions {where} "
            "GROUP BY category, type ORDER BY total DESC",
            params,
        ).fetchall()
        income = round(totals["total_income"], 2)
        expenses = round(totals["total_expenses"], 2)
        return jsonify({
            "total_income": income,
            "total_expenses": expenses,
            "balance": round(income - expenses, 2),
            "transaction_count": totals["transaction_count"],
            "by_category": [row_to_dict(r) for r in by_category],
        })

    @app.get("/api/categories")
    def categories():
        rows = db.get_db().execute(
            "SELECT DISTINCT category FROM transactions ORDER BY category"
        ).fetchall()
        return jsonify({"categories": [r["category"] for r in rows]})

    # ---------- error handlers ----------
    @app.errorhandler(404)
    def not_found(_e):
        return error("Resource not found.", 404)

    @app.errorhandler(405)
    def method_not_allowed(_e):
        return error("Method not allowed.", 405)

    @app.errorhandler(sqlite3.Error)
    def database_error(_e):
        return error("A database error occurred.", 500)

    @app.errorhandler(Exception)
    def unexpected(e):
        if isinstance(e, HTTPException):
            return error(e.description, e.code)
        app.logger.exception("Unhandled error")
        return error("Internal server error.", 500)

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
