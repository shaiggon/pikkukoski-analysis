import datetime as dt

from app.weather import iter_date_ranges


def test_iter_date_ranges_chunks_without_gaps_or_overlap() -> None:
    start = dt.datetime(2025, 6, 1, 0, 0, tzinfo=dt.timezone.utc)
    end = dt.datetime(2025, 6, 3, 12, 0, tzinfo=dt.timezone.utc)

    ranges = iter_date_ranges(
        start_time=start,
        end_time=end,
        step=dt.timedelta(hours=24),
    )

    assert ranges == [
        (dt.datetime(2025, 6, 1, 0, 0, tzinfo=dt.timezone.utc), dt.datetime(2025, 6, 2, 0, 0, tzinfo=dt.timezone.utc)),
        (dt.datetime(2025, 6, 2, 0, 0, tzinfo=dt.timezone.utc), dt.datetime(2025, 6, 3, 0, 0, tzinfo=dt.timezone.utc)),
        (dt.datetime(2025, 6, 3, 0, 0, tzinfo=dt.timezone.utc), dt.datetime(2025, 6, 3, 12, 0, tzinfo=dt.timezone.utc)),
    ]
