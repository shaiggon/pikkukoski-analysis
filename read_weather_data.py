import pandas as pd
from datetime import datetime

def read_weather_data(weather_file: str) -> pd.DataFrame:
  df = pd.read_csv(weather_file)
  df["date"] = df["Vuosi"].astype(str) + "-" + df["Kuukausi"].astype(str).str.zfill(2) + "-" + df["Päivä"].astype(str).str.zfill(2) +  " " + df["Aika [Paikallinen aika]"]
  df["date"] = pd.to_datetime(df["date"], format='%Y-%m-%d %H:%M')

  df.drop(columns=["Vuosi", "Kuukausi", "Päivä", "Aika [Paikallinen aika]"], inplace=True)
  df["Sademäärä [mm]"] = pd.to_numeric(df["Sademäärä [mm]"], errors='coerce')
  df["Ilman lämpötila [°C]"] = pd.to_numeric(df["Ilman lämpötila [°C]"], errors='coerce')

  df.set_index("date", inplace=True)

  return df

def resample_weather_data(weather_df: pd.DataFrame, resample_rate: str) -> pd.DataFrame:
  """
  Resample rate is the same that is used in pandas (for example every 30min the string is "30min")
  """
  aggregated_weather = weather_df.resample(resample_rate).agg({
    "Sademäärä [mm]": "sum",
    "Ilman lämpötila [°C]": "mean"
  })

  return aggregated_weather


def main():
  df = read_weather_data("Helsinki Kumpula_ 25.5.2023 - 30.8.2023_d6f3d181-df41-42ba-b2eb-77d9b687db9d.csv")
  print(df)

if __name__ == "__main__":
  main()