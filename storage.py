import json
import os
from config import DB_PATH


def _load():
    if not os.path.exists(DB_PATH):
        return {}
    with open(DB_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _save(data):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_invoice(invoice_id: str, user_id: int, plan_id: str):
    data = _load()
    data[str(invoice_id)] = {
        "user_id": user_id,
        "plan_id": plan_id,
        "status": "created",
    }
    _save(data)


def mark_paid(invoice_id: str):
    data = _load()
    if str(invoice_id) in data:
        data[str(invoice_id)]["status"] = "paid"
        _save(data)


def is_paid(invoice_id: str) -> bool:
    data = _load()
    entry = data.get(str(invoice_id))
    return bool(entry and entry.get("status") == "paid")


def get_plan_id(invoice_id: str):
    data = _load()
    entry = data.get(str(invoice_id))
    return entry.get("plan_id") if entry else None
