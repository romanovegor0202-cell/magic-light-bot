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
    import re

    value = value.strip().lower()

    months = {
        "января": 1,
        "январь": 1,
        "янв": 1,
        "февраля": 2,
        "февраль": 2,
        "фев": 2,
        "марта": 3,
        "март": 3,
        "мар": 3,
        "апреля": 4,
        "апрель": 4,
        "апр": 4,
        "мая": 5,
        "май": 5,
        "май": 5,
        "июня": 6,
        "июнь": 6,
        "июн": 6,
        "июля": 7,
        "июль": 7,
        "июл": 7,
        "августа": 8,
        "август": 8,
        "авг": 8,
        "сентября": 9,
        "сентябрь": 9,
        "сен": 9,
        "сент": 9,
        "октября": 10,
        "октябрь": 10,
        "окт": 10,
        "ноября": 11,
        "ноябрь": 11,
        "ноя": 11,
        "декабря": 12,
        "декабрь": 12,
        "дек": 12,
    }

    # Даты с цифровым месяцем:
    # 04.10.26
    # 04 10 26
    # 04-10-26
    # 04/10/26
    match = re.fullmatch(
        r"(\d{1,2})[\s./-]+(\d{1,2})[\s./-]+(\d{2}|\d{4})",
        value
    )

    if match:
        day, month, year = match.groups()

        day = int(day)
        month = int(month)
        year = int(year)

        if year < 100:
            year += 2000

        try:
            return datetime(year, month, day).date()
        except ValueError:
            raise ValueError(f"Invalid event date: {value}")

    # Даты с названием месяца:
    # 04 октября 26
    # 4 октября 2026
    # 04 окт 26
    match = re.fullmatch(
        r"(\d{1,2})\s+([а-яё]+)\s+(\d{2}|\d{4})",
        value
    )

    if match:
        day, month_name, year = match.groups()

        if month_name not in months:
            raise ValueError(f"Unknown month: {month_name}")

        day = int(day)
        month = months[month_name]
        year = int(year)

        if year < 100:
            year += 2000

        try:
            return datetime(year, month, day).date()
        except ValueError:
            raise ValueError(f"Invalid event date: {value}")

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
