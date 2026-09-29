import base64
import json
import os
from datetime import datetime, timedelta

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


def _credentials():
    raw = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_B64", "").strip()
    if not raw:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON_B64 is not configured")
    data = json.loads(base64.b64decode(raw).decode("utf-8"))
    return service_account.Credentials.from_service_account_info(data, scopes=SCOPES)


def _parse_date(value: str):
    for fmt in ("%d.%m.%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Unsupported event date: {value}")


def create_order_event(order: dict) -> str:
    calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "").strip()
    if not calendar_id:
        raise RuntimeError("GOOGLE_CALENDAR_ID is not configured")

    credentials = _credentials()
    service = build("calendar", "v3", credentials=credentials, cache_discovery=False)

    event_date = _parse_date(order["event_date"])
    start = event_date.isoformat()
    end = (event_date + timedelta(days=1)).isoformat()

    items = json.loads(order["items_json"])
    item_lines = []
    for item in items:
        if item["line_min"] == item["line_max"]:
            price = f'{item["line_min"]:,}'.replace(",", " ")
        else:
            price = f'от {item["line_min"]:,} до {item["line_max"]:,}'.replace(",", " ")
        item_lines.append(f'• {item["name"]} — {item["quantity"]} × — {price} ₽')

    total = (
        f'{order["total_min"]:,}'.replace(",", " ")
        if order["total_min"] == order["total_max"]
        else f'от {order["total_min"]:,} до {order["total_max"]:,}'.replace(",", " ")
    )

    description = "\n".join([
        f'Заказ №{order["id"]}',
        f'Клиент: {order["name"]}',
        f'Телефон: {order["phone"]}',
        f'Дата мероприятия: {order["event_date"]}',
        f'Место: {order["venue"]}',
        "",
        "ЗАКАЗ:",
        *item_lines,
        "",
        f'ИТОГО: {total} ₽',
        *(["", f'Комментарий: {order["comment"]}'] if order.get("comment") else []),
    ])

    event = {
        "id": f'magiclightorder{order["id"]}',
        "summary": f'Magic Light — заказ №{order["id"]} — {order["name"]}',
        "location": order["venue"],
        "description": description,
        "start": {"date": start},
        "end": {"date": end},
    }

    try:
        created = service.events().insert(calendarId=calendar_id, body=event).execute()
        return created.get("htmlLink", "")
    except HttpError as exc:
        if getattr(exc, "status_code", None) == 409 or getattr(exc.resp, "status", None) == 409:
            existing = service.events().get(calendarId=calendar_id, eventId=event["id"]).execute()
            return existing.get("htmlLink", "")
        raise
