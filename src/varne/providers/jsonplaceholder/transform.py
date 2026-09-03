import json
from datetime import UTC, datetime


def transform_posts(posts: str) -> list[dict]:
    now = datetime.now(UTC)
    rows = []

    for post in json.loads(posts):
        row = {
            "provider": "jsonplaceholder",
            "event_time": now,
            "amount": float(len(post["body"])),
        }
        rows.append(row)

    return rows
