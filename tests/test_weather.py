import datetime as dt

from app.weather import parse_fmi_response


def test_parse_fmi_response_extracts_records() -> None:
    xml = """
    <wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs/2.0"
                           xmlns:wml2="http://www.opengis.net/waterml/2.0"
                           xmlns:gml="http://www.opengis.net/gml/3.2">
      <wfs:member>
        <gml:name>kumpula</gml:name>
        <wml2:MeasurementTimeseries>
          <wml2:point>
            <wml2:MeasurementTVP>
              <wml2:time>2026-05-01T00:00:00Z</wml2:time>
              <wml2:value>1.2</wml2:value>
            </wml2:MeasurementTVP>
          </wml2:point>
        </wml2:MeasurementTimeseries>
      </wfs:member>
    </wfs:FeatureCollection>
    """
    records = parse_fmi_response(xml, fetched_at=dt.datetime(2026, 5, 1, tzinfo=dt.timezone.utc))

    assert len(records) == 1
    assert records[0]["station_id"] == "kumpula"
    assert records[0]["rain_mm"] == 1.2

