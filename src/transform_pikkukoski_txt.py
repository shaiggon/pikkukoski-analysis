import pandas as pd
from datetime import datetime

"""
The pikkukoski_<year>.txt files are basically the pikkukoski part taken from these pdfs
https://www.hel.fi/static/liitteet/kaupunkiymparisto/kulttuuri-ja-vapaa-aika/uimarannat/Uimavedenlaatu_2024.pdf
https://www.hel.fi/static/liitteet/kaupunkiymparisto/kulttuuri-ja-vapaa-aika/uimarannat/Uimavedenlaatu_2023.pdf
and have the ", lisänäyte" or ", uusinta" removed. These txt files are created manually.

We want to make these into a more standard format (csv)

The other beaches (tapaninvainio and pakila) follow the same convention
"""

def parse_line(line: str) -> list:
  """
  Parse one line of the txt file
  """
  parts = line.split()
  date_str = parts[0]
  date = datetime.strptime(date_str, '%d.%m.%Y')
  quality = int(parts[1] == "Hyvä/bra/good")
  temperature = float(parts[2].replace(",", "."))
  enterococci = float(parts[3])
  ecoli = float(parts[4])
  blue_green_algae = int(parts[5])
  other_observations = int(parts[6])
  return [date, quality, temperature, enterococci, ecoli, blue_green_algae, other_observations]

def process_file(pikkukoski_filename: str):
  """
  Process a txt file copied from a pdf to a more standard csv
  """
  with open(pikkukoski_filename, "r") as pkf:
    lines = pkf.readlines()
  data = [parse_line(line) for line in lines]
  columns = ["date", "quality", "temperature", "enterococci", "ecoli", "blue_green_algae", "other_observations"]
  df = pd.DataFrame(data, columns=columns)
  df["date"] = pd.to_datetime(df["date"])

  print(df)

  csv_filename = pikkukoski_filename.split(".txt")[0] + ".csv"
  df.to_csv(csv_filename)

  print(f"Saved pikkukoski water quality to file ${csv_filename}")

def main():
  #process_file("../data/pikkukoski_2023.txt")
  #process_file("../data/pikkukoski_2024.txt")
  #process_file("../data/tapaninvainio_2023.txt")
  #process_file("../data/pakila_2023.txt")
  #process_file("../data/pikkukoski_2021.txt")
  #process_file("../data/pikkukoski_2022.txt")
  #process_file("../data/tapaninvainio_2021.txt")
  #process_file("../data/tapaninvainio_2022.txt")
  #process_file("../data/pakila_2021.txt")
  #process_file("../data/pakila_2022.txt")
  process_file("../data/pakila_2024.txt")
  process_file("../data/tapaninvainio_2024.txt")

if __name__ == "__main__":
  main()