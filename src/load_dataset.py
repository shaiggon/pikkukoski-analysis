import pandas as pd
from read_weather_data import read_weather_data, resample_weather_data
from read_pikkukoski_measurement import read_pikkukoski_measurement

def weather_with_lag(df: pd.DataFrame, number_of_lag_features: int = 5, rolling_window: int = 5) -> pd.DataFrame:
  """
  The timeframe that the lag features account for are based on the sample rate of dt.
  Also have rolling average and sum.
  """
  df_with_lag = df.copy()
  rain_lag_name = "rain_lag"
  for i in range(number_of_lag_features):
    df_with_lag[f"{rain_lag_name}{i + 1}"] = df["Sademäärä [mm]"].shift(i + 1)
  
  df_with_lag[f"rain_rolling_sum{rolling_window}"] = df["Sademäärä [mm]"].rolling(window=rolling_window).sum()
  df_with_lag[f"rain_rolling_mean{rolling_window}"] = df["Sademäärä [mm]"].rolling(window=rolling_window).mean()

  # Rename current rain amount
  df_with_lag.rename(columns={"Sademäärä [mm]": "rain_now"}, inplace=True)

  if "Ilman lämpötila [°C]" in df_with_lag.columns:
    df_with_lag = df_with_lag.drop(columns=["Ilman lämpötila [°C]"])

  return df_with_lag

def rename_columns_and_drop_name_for_station(df: pd.DataFrame, station_name: str) -> pd.DataFrame:
  """
  Rename weather observation columns by prepending weather station name
  """
  # All renamed column names start with "rain_"
  renamed_columns = [col for col in df if col.startswith("rain_")]
  renamed_df = df.copy()
  renames = {}
  for col in renamed_columns:
    renames[col] = f"{station_name}_{col}"
  renamed_df.rename(columns=renames, inplace=True)
  return renamed_df

def combine_weather_observations(stations_observations: list[pd.DataFrame], observation_station_names: list[str]) -> pd.DataFrame:
  """
  Combine different weather stations observations per year
  Renames also the columns such that each can be traced to one station
  """
  merged_observations = rename_columns_and_drop_name_for_station(stations_observations[0], observation_station_names[0])
  for i in range(1, len(observation_station_names)):
    merged_observations = pd.merge(merged_observations, rename_columns_and_drop_name_for_station(stations_observations[i], observation_station_names[i]), on="date", how="inner")
  return merged_observations

def rename_measurement_and_drop(df: pd.DataFrame, beach_name: str) -> pd.DataFrame:
  renamed_df = df.copy()
  renamed_df.rename(columns={"enterococci": f"enterococci_{beach_name}", "ecoli": f"ecoli_{beach_name}", "quality": f"quality_{beach_name}"}, inplace=True)
  renamed_df = renamed_df.drop(columns=["temperature", "blue_green_algae", "other_observations"])
  return renamed_df

def combine_measurements(measurements: list[pd.DataFrame], beach_names = list[str]) -> pd.DataFrame:
  merged = rename_measurement_and_drop(measurements[0], beach_names[0])
  for i in range(1, len(beach_names)):
    merged = pd.merge(merged, rename_measurement_and_drop(measurements[i], beach_names[i]), on="date", how="inner")
  return merged

def load_dataset(weather_files: dict, measurement_files: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
  """
  Load X and Y. Do train and test split later.
  Dicts given to the function are structured as such (key is always the observation station name, list length must be same, year order must be same):
  {
    "kumpula": ["kumpula2021.csv", "kumpula2022.csv"],
    "helsinki-vantaa": ["helsinki-vantaa2021.csv", "helsinki-vantaa2022.csv"],
  }
  """
  RESAMPLE_RATE = "12h"
  ROLLING_WINDOW = 10
  LAG_FEATURES = 5
  weather_station_names = []
  weather_observations = {}
  for key in weather_files:
    weather_station_names.append(key)
    weather_observations[key] = [weather_with_lag(resample_weather_data(read_weather_data(filename), RESAMPLE_RATE), LAG_FEATURES, ROLLING_WINDOW) for filename in weather_files[key]]
  
  measurement_beach_names = []
  measurements = {}
  for key in measurement_files:
    measurement_beach_names.append(key)
    measurements[key] = [read_pikkukoski_measurement(filename) for filename in measurement_files[key]]

  # Get length of observations per station
  observation_years = len(weather_observations[next(iter(weather_observations))])
  assert(observation_years == len(measurement_files[next(iter(measurement_files))]))

  combined_year_observations = []
  combined_year_measurements = []
  observations_and_measurements_for_years = []
  for year_index in range(observation_years):
    # Weather data
    weather_observations_for_year = [weather_observations[observation_key][year_index] for observation_key in weather_observations.keys()]
    combined_observations_for_year = combine_weather_observations(weather_observations_for_year, weather_station_names)
    #combined_year_observations.append(combined_observations_for_year)
    # Water quality measurement data
    measurements_for_year = [measurements[key][year_index] for key in measurements.keys()]
    combined_measurements_for_year = combine_measurements(measurements_for_year, measurement_beach_names)
    #combined_year_measurements.append(combined_measurements_for_year)
    observations_and_measurements_for_years.append(pd.merge(combined_observations_for_year, combined_measurements_for_year, on="date", how="inner"))
  
  all_observations_and_measurements = pd.concat(observations_and_measurements_for_years)
  x_feature_names = [col for col in all_observations_and_measurements if "rain_" in col]

  #print(all_observations_and_measurements.columns)
  
  X = all_observations_and_measurements[x_feature_names]
  Y = all_observations_and_measurements.drop(columns=x_feature_names)

  return X, Y

def get_filenames() -> tuple[dict, dict]:
  PIKKUKOSKI_2024 = "../data/pikkukoski_2024.csv"
  PAKILA_2024 = "../data/pakila_2024.csv"
  TAPANINVAINIO_2024 = "../data/tapaninvainio_2024.csv"

  PIKKUKOSKI_2023 = "../data/pikkukoski_2023.csv"
  PAKILA_2023 = "../data/pakila_2023.csv"
  TAPANINVAINIO_2023 = "../data/tapaninvainio_2023.csv"

  PIKKUKOSKI_2022 = "../data/pikkukoski_2022.csv"
  PAKILA_2022 = "../data/pakila_2022.csv"
  TAPANINVAINIO_2022 = "../data/tapaninvainio_2022.csv"

  PIKKUKOSKI_2021 = "../data/pikkukoski_2021.csv"
  PAKILA_2021 = "../data/pakila_2021.csv"
  TAPANINVAINIO_2021 = "../data/tapaninvainio_2021.csv"

  KUMPULA_2021 = "../data/Helsinki Kumpula_ 25.5.2021 - 30.8.2021_c125b1e6-d253-4d56-9c10-880a6f6e198a.csv"
  KUMPULA_2022 = "../data/Helsinki Kumpula_ 25.5.2022 - 30.8.2022_c7ee589b-5a8d-420d-82e5-3ecf704f71f0.csv"
  KUMPULA_2023 = "../data/Helsinki Kumpula_ 25.5.2023 - 30.8.2023_d6f3d181-df41-42ba-b2eb-77d9b687db9d.csv"
  KUMPULA_2024 = "../data/Helsinki Kumpula_ 25.5.2024 - 25.6.2024_3733a5d6-a008-4858-9a88-88e3d33415e8.csv"

  HELSINKI_VANTAA_2021 = "../data/Vantaa Helsinki-Vantaan lentoasema_ 25.5.2021 - 30.8.2021_e667c023-1a8c-49c9-a70a-55ebcf553c48.fixed.csv"
  HELSINKI_VANTAA_2022 = "../data/Vantaa Helsinki-Vantaan lentoasema_ 25.5.2022 - 30.8.2022_3eb7a63b-d960-425f-8463-903cf05b0945.csv"
  HELSINKI_VANTAA_2023 = "../data/Vantaa Helsinki-Vantaan lentoasema_ 25.5.2023 - 30.8.2023_195d7189-8a24-408e-832d-35df526886af.csv"
  HELSINKI_VANTAA_2024 = "../data/Vantaa Helsinki-Vantaan lentoasema_ 25.5.2024 - 25.6.2024_fe257415-f7da-404c-803d-a9b6cf0f3b5f.csv"

  weather_files = {"helsinki-vantaa": [HELSINKI_VANTAA_2021, HELSINKI_VANTAA_2022, HELSINKI_VANTAA_2023, HELSINKI_VANTAA_2024],
                   "kumpula": [KUMPULA_2021, KUMPULA_2022, KUMPULA_2023, KUMPULA_2024]}
  measurement_files = {
    "pikkukoski": [PIKKUKOSKI_2021, PIKKUKOSKI_2022, PIKKUKOSKI_2023, PIKKUKOSKI_2024],
    "pakila": [PAKILA_2021, PAKILA_2022, PAKILA_2023, PAKILA_2024],
    "tapaninvainio": [TAPANINVAINIO_2021, TAPANINVAINIO_2022, TAPANINVAINIO_2023, TAPANINVAINIO_2024]
  }

  return weather_files, measurement_files


def main():
  weather_files, measurement_files = get_filenames()

  X, Y = load_dataset(weather_files, measurement_files)

  print("Print X")
  print(X)
  print("Print Y")
  print(Y)

if __name__ == "__main__":
  main()