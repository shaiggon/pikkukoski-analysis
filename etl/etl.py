import requests
import pandas as pd
import datetime
import xml.etree.ElementTree as ET
from typing import Optional
# TODO: Add moto and boto3 (or use sqlite or something)

WEATHER_API_URL = "https://opendata.fmi.fi/wfs/fin"
ETL_WEATHER_FILENAME = "etl_weather_data.parquet"

def get_weather(first_one: bool) -> Optional[pd.DataFrame]:
  history_hours = 126 if first_one else 4
  params = {
    "service": "WFS",
    "version": "2.0.0",
    "request": "getFeature",
    "parameters": "PRA_PT1H_ACC",
    "timestep": "60",
    "storedquery_id": "fmi::observations::weather::hourly::timevaluepair",
    "starttime": (datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=history_hours)).strftime('%Y-%m-%dT%H:%M:%SZ'),
    "endtime": datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%dT%H:%M:%SZ'),
    "place": ["kumpula", "helsinki-vantaan_lentoasema"],
  }
  response = requests.get(WEATHER_API_URL, params=params)

  if response.status_code == 200:
    #print(response.text)
    return transform(response.text)
  else:
    print(f"Error: {response.status_code}: {response.text}")
    return None

def transform(data: str) -> pd.DataFrame:
  """
  Transform the resulting xml text from fmi to a DataFrame only saving the wanted data (rain amount per hour for the wanted stations)
  """
  records = []
  root = ET.fromstring(data)
  ns = {
    "wml2": "http://www.opengis.net/waterml/2.0",
    "wfs": "http://www.opengis.net/wfs/2.0",
    "gml": "http://www.opengis.net/gml/3.2",
  }
  for member in root.findall('wfs:member', ns):
    # print(f"member: {member}")
    for measurement in member.findall(".//wml2:MeasurementTimeseries", ns):
      # print(measurement)
      for point in measurement.findall(".//wml2:point", ns):
        # print(f"time: {point.find(".//wml2:time", ns)}")
        record = {
          "timestamp": point.find(".//wml2:time", ns).text,
          "location": member.find(".//gml:name", ns).text,
          "rain": point.find(".//wml2:value", ns).text
        }
        records.append(record)

  df = pd.DataFrame(records)
  return df

def read_previous_weather() -> Optional[pd.DataFrame]:
  """
  I wonder if there should be a function for both reading this from local file system as well as from S3 (or other object storage)
  """
  try:
    df = pd.read_parquet(ETL_WEATHER_FILENAME)
    return df
  except FileNotFoundError: # File not yet created, ok case, just don't return anything
    return None

def save_new_weather(df: pd.DataFrame):
  df.to_parquet(ETL_WEATHER_FILENAME)
  print(f"Saved etl result to {ETL_WEATHER_FILENAME}")

def main():
  previous_weather = read_previous_weather()

  df: pd.DataFrame
  if previous_weather is not None:
    df = get_weather(first_one=False)
  else:
    df = get_weather(first_one=True)

  if df is not None:
    # Process the newly fetched data
    df[["timestamp"]] = df[["timestamp"]].apply(pd.to_datetime)
    df.set_index("timestamp", inplace=True)
    df[["rain"]] = df[["rain"]].apply(pd.to_numeric, errors='coerce')
    df.sort_values(by="timestamp", inplace=True)

    # Combine previous measurements with newly fetched data
    if previous_weather is not None:
      previous_weather = previous_weather[~previous_weather.index.isin(df.index)]
      df = pd.concat([previous_weather, df])

    # Fill NaN only after combining new and old data
    df[["rain"]] = df.groupby("location")[["rain"]].ffill()
    save_new_weather(df)

if __name__ == "__main__":
  main()