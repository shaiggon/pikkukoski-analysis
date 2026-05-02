from app.measurements import quality_int_to_label


def test_quality_int_to_label() -> None:
    assert quality_int_to_label(1) == "good"
    assert quality_int_to_label(0) == "poor"

