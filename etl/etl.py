import requests
import pandas as pd
import datetime
import xml.etree.ElementTree as ET
# TODO: Add moto and boto3

WEATHER_API_URL = "https://opendata.fmi.fi/wfs/fin"

def get_weather(first_one: bool) -> pd.DataFrame:
  history_hours = 126 if first_one else 1
  params = {
    "service": "WFS",
    "version": "2.0.0",
    "request": "getFeature",
    #"parameters": "temperature",
    "parameters": "PRA_PT1H_ACC",
    "timestep": "60",
    "storedquery_id": "fmi::observations::weather::hourly::timevaluepair",
    "starttime": (datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=history_hours)).strftime('%Y-%m-%dT%H:%M:%SZ'),
    "endtime": datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%dT%H:%M:%SZ'),
    "place": ["kumpula", "helsinki-vantaan_lentoasema"],
    #"place": "helsinki-vantaan_lentoasema",
  }
  response = requests.get(WEATHER_API_URL, params=params)

  if response.status_code == 200:
    print(response)
    print(response.text)
    return transform(response.text)
    #data = response.json()
    #print(data)
  else:
    print(f"Error: {response.status_code}: {response.text}")
    return None


def transform(data: str) -> pd.DataFrame:
  records = []
  root = ET.fromstring(data)
  ns = {
    "wml2": "http://www.opengis.net/waterml/2.0",
    "wfs": "http://www.opengis.net/wfs/2.0",
    "gml": "http://www.opengis.net/gml/3.2",
  }
  for member in root.findall('wfs:member', ns):
    print(f"member: {member}")
    for measurement in member.findall(".//wml2:MeasurementTimeseries", ns):
      print(measurement)
      for point in member.findall(".//wml2:point", ns):
        print(f"time: {point.find(".//wml2:time", ns)}")
        record = {
          "timestamp": point.find(".//wml2:time", ns).text,
          "location": member.find(".//gml:name", ns).text,
          "rain": point.find(".//wml2:value", ns).text
        }
        records.append(record)

  df = pd.DataFrame(records)
  return df

def main():
  df = get_weather(first_one=True)
  print(df)

if __name__ == "__main__":
  main()