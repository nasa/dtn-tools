from datetime import datetime, timezone


def DtnTimeNowMs():
    """Return the current DTN time, in milliseconds."""
    dt = datetime.now(tz=timezone.utc) - datetime(2000, 1, 1, tzinfo=timezone.utc)
    return int(dt.total_seconds() * 1000)
