import json

from varne.providers.jsonplaceholder.transform import transform_posts


def test_transform_posts():
    post_list = [
        {
            "id": 123,
            "userId": 7,
            "title": "Hello",
            "body": "abcdef",
        }
    ]

    post_str = json.dumps(post_list)

    rows = transform_posts(post_str)

    assert len(rows) == 1

    row = rows[0]

    assert row.id == "jsonplaceholder"
    assert row.amount == len("abcdef")
