import json
from datetime import UTC, datetime

from varne.providers.types import RowStaging


def transform_posts(posts: str) -> list[RowStaging]:
    now = datetime.now(UTC)
    rows = []

    for post in json.loads(posts):
        row = RowStaging(
            id="jsonplaceholder",
            event_time=now,
            amount=float(len(post.get("body"))),
        )
        rows.append(row)

    return rows
