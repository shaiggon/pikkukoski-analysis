import pandas as pd
from datetime import datetime

def read_weather_data(weather_file: str) -> pd.DataFrame:
  df = pd.read_csv(weather_file)
  df["date"] = df["Vuosi"].astype(str) + "-" + df["Kuukausi"].astype(str).str.zfill(2) + "-" + df["Päivä"].astype(str).str.zfill(2) +  " " + df["Aika [Paikallinen aika]"]
  df["date"] = pd.to_datetime(df["date"], format='%Y-%m-%d %H:%M')

  df.drop(columns=["Vuosi", "Kuukausi", "Päivä", "Aika [Paikallinen aika]"], inplace=True)
  df["Sademäärä [mm]"] = pd.to_numeric(df["Sademäärä [mm]"], errors='coerce')
  if "Ilman lämpötila [°C]" in df.columns:
    df["Ilman lämpötila [°C]"] = pd.to_numeric(df["Ilman lämpötila [°C]"], errors='coerce')

  df.set_index("date", inplace=True)

  return df

def resample_weather_data(weather_df: pd.DataFrame, resample_rate: str) -> pd.DataFrame:
  """
  Resample rate is the same that is used in pandas (for example every 30min the string is "30min")
  """
  agg_dict = {
    "Sademäärä [mm]": "sum"
  }

  if "Ilman lämpötila [°C]" in weather_df.columns:
    agg_dict["Ilman lämpötila [°C]"] = "mean"

  aggregated_weather = weather_df.resample(resample_rate).agg(agg_dict)

  return aggregated_weather


def fix_weather_data(weather_data_filename: str, fixed_weather_data_filename: str):
  """
  Sometimes the weather file has missing data points. Let's fix those by copying the previous rain amount to the current measurement.
  Luckily the timestamps exist for the missing data but the measurement station and the rain amount are missing.
  The missing data points have corrupted data for the first and last columns for the csv. I'm not reading the file as a csv due to
  this being easier although fixing the file this way is arguably very hacky.
  """
  new_lines = []
  with open(weather_data_filename, "r") as wf:
    previous_measurement: str = ""
    previous_station: str = ""
    for line in wf:
      split_line = line.split(",")
      new_line = line
      if split_line[0] != "\"-\"": # Every corrupted line starts with "-"
        previous_measurement = split_line[-1] # Last value is the measurement
        previous_station = split_line[0] # First value is the station
      else:
        new_line = ",".join([previous_station] + split_line[0:-1] + [previous_measurement])
      new_lines.append(new_line)
  with open(fixed_weather_data_filename, "w") as ff:
    ff.writelines(new_lines)




def main():
  df = read_weather_data("../data/Helsinki Kumpula_ 25.5.2023 - 30.8.2023_d6f3d181-df41-42ba-b2eb-77d9b687db9d.csv")
  print(df)

  print("fix file")
  fix_weather_data("../data/Vantaa Helsinki-Vantaan lentoasema_ 25.5.2021 - 30.8.2021_e667c023-1a8c-49c9-a70a-55ebcf553c48.csv", "../data/Vantaa Helsinki-Vantaan lentoasema_ 25.5.2021 - 30.8.2021_e667c023-1a8c-49c9-a70a-55ebcf553c48.fixed.csv")

if __name__ == "__main__":
  main()