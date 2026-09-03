import ibis

from varne.db.schema import TableStaging


def get_usage_by_id(db: ibis.BaseBackend):
    staging = db.table(TableStaging().name)

    records = staging.group_by("id").aggregate(total_amount=staging.amount.sum())

    return records
