import pandas as pd

from etl.etl import combine_weather, normalise_weather_frame


def test_normalise_weather_frame_sorts_index_after_setting_timestamp() -> None:
    frame = pd.DataFrame(
        [
            {"timestamp": "2024-06-02T01:00:00Z", "location": "kumpula", "rain": "2.0"},
            {"timestamp": "2024-06-02T00:00:00Z", "location": "kumpula", "rain": "1.0"},
        ]
    )

    result = normalise_weather_frame(frame)

    assert list(result.index.astype(str)) == [
        "2024-06-02 00:00:00+00:00",
        "2024-06-02 01:00:00+00:00",
    ]
    assert list(result["rain"]) == [1.0, 2.0]


def test_combine_weather_keeps_other_station_when_new_fetch_is_partial() -> None:
    previous = pd.DataFrame(
        [
            {"timestamp": "2024-06-02T00:00:00Z", "location": "kumpula", "rain": 1.0},
            {"timestamp": "2024-06-02T00:00:00Z", "location": "helsinki-vantaan_lentoasema", "rain": 3.0},
        ]
    )
    new = pd.DataFrame(
        [
            {"timestamp": "2024-06-02T00:00:00Z", "location": "kumpula", "rain": 1.5},
        ]
    )

    combined = combine_weather(
        normalise_weather_frame(previous),
        normalise_weather_frame(new),
    ).reset_index()

    assert len(combined) == 2
    assert combined.loc[combined["location"] == "kumpula", "rain"].iloc[0] == 1.5
    assert combined.loc[
        combined["location"] == "helsinki-vantaan_lentoasema", "rain"
    ].iloc[0] == 3.0
