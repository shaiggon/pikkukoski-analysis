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

def normalise_weather_frame(df: pd.DataFrame) -> pd.DataFrame:
  """
  Convert raw weather data into the parquet shape used by the ETL.
  """
  normalised = df.copy()
  if "timestamp" in normalised.columns:
    normalised["timestamp"] = pd.to_datetime(normalised["timestamp"])
    normalised.set_index("timestamp", inplace=True)
  else:
    normalised.index = pd.to_datetime(normalised.index)
    normalised.index.name = "timestamp"

  normalised[["rain"]] = normalised[["rain"]].apply(pd.to_numeric, errors='coerce')
  normalised.sort_index(inplace=True)
  return normalised

def combine_weather(previous_weather: pd.DataFrame, new_weather: pd.DataFrame) -> pd.DataFrame:
  """
  Merge old and new observations without losing one station when only the other
  station appears in an overlapping fetch window.
  """
  previous_reset = previous_weather.reset_index()
  new_reset = new_weather.reset_index()
  combined = pd.concat([previous_reset, new_reset], ignore_index=True)
  combined.drop_duplicates(subset=["timestamp", "location"], keep="last", inplace=True)
  combined.sort_values(by=["timestamp", "location"], inplace=True)
  combined.set_index("timestamp", inplace=True)
  return combined

def main():
  previous_weather = read_previous_weather()

  df: pd.DataFrame
  if previous_weather is not None:
    df = get_weather(first_one=False)
  else:
    df = get_weather(first_one=True)

  if df is not None:
    # Process the newly fetched data
    df = normalise_weather_frame(df)

    # Combine previous measurements with newly fetched data
    if previous_weather is not None:
      previous_weather = normalise_weather_frame(previous_weather)
      df = combine_weather(previous_weather, df)

    # Fill NaN only after combining new and old data
    df.sort_index(inplace=True)
    df[["rain"]] = df.groupby("location")[["rain"]].ffill()
    save_new_weather(df)

if __name__ == "__main__":
  main()
