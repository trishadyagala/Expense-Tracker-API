"""Input validation. Each function returns (clean_data, errors)."""
from datetime import date, datetime

VALID_TYPES = ("income", "expense")


def _parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    except (TypeError, ValueError):
        return None


def validate_transaction(payload, partial=False):
    """Validate a create (partial=False) or update (partial=True) payload."""
    errors = {}
    clean = {}

    if not isinstance(payload, dict):
        return {}, {"body": "Request body must be a JSON object."}

    required = ("type", "amount", "category")
    if not partial:
        for field in required:
            if field not in payload:
                errors[field] = "This field is required."

    if "type" in payload:
        t = str(payload["type"]).strip().lower()
        if t not in VALID_TYPES:
            errors["type"] = "Must be 'income' or 'expense'."
        else:
            clean["type"] = t

    if "amount" in payload:
        try:
            amount = float(payload["amount"])
            if isinstance(payload["amount"], bool) or amount <= 0:
                raise ValueError
            clean["amount"] = round(amount, 2)
        except (TypeError, ValueError):
            errors["amount"] = "Must be a positive number."

    if "category" in payload:
        category = str(payload["category"]).strip().lower()
        if not category or len(category) > 50:
            errors["category"] = "Must be 1-50 characters."
        else:
            clean["category"] = category

    if "description" in payload:
        description = str(payload["description"]).strip()
        if len(description) > 255:
            errors["description"] = "Must be at most 255 characters."
        else:
            clean["description"] = description

    if "date" in payload:
        parsed = _parse_date(payload["date"])
        if parsed is None:
            errors["date"] = "Must be a valid date in YYYY-MM-DD format."
        else:
            clean["date"] = parsed
    elif not partial:
        clean["date"] = date.today().isoformat()

    if partial and not clean and not errors:
        errors["body"] = "Provide at least one field to update."

    return clean, errors


def validate_filters(args):
    """Validate query-string filters shared by the list and summary endpoints."""
    errors = {}
    clean = {}

    if args.get("type"):
        t = args["type"].strip().lower()
        if t not in VALID_TYPES:
            errors["type"] = "Must be 'income' or 'expense'."
        else:
            clean["type"] = t

    if args.get("category"):
        clean["category"] = args["category"].strip().lower()

    for key in ("start_date", "end_date"):
        if args.get(key):
            parsed = _parse_date(args[key])
            if parsed is None:
                errors[key] = "Must be a valid date in YYYY-MM-DD format."
            else:
                clean[key] = parsed

    if "start_date" in clean and "end_date" in clean and clean["start_date"] > clean["end_date"]:
        errors["start_date"] = "start_date must not be after end_date."

    return clean, errors
