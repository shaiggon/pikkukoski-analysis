import pandas as pd

def read_pikkukoski_measurement(measurement_filename: str, hour_of_measurement: int = 0) -> pd.DataFrame:
  df = pd.read_csv(measurement_filename)
  df["date"] = pd.to_datetime(df["date"])
  df.set_index("date", inplace=True)
  df.index = df.index + pd.Timedelta(hours=hour_of_measurement)
  return df
