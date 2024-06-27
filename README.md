# Pikkukoski water quality analysis

Pikkukoski is a small beach in Helsinki along River Vantaanjoki. Swimming there is refreshing and the surrounding is
a magical little plot of nature in the city.

Pikkukoski also has a problem with its water quality during and after heavy rains. It can thus sometimes be difficult to figure
out whether or not it is safe to swim there. As the water quality measurements are sparse there is no real-time information
available of the swimmability of the water.

The purpose of this project is to figure out if we can predict the water quality given weather data.
As the data points for the measurements are not frequent, I suspect that a simple and interpretable model would make
the most sense to use here.

If it seems to be possible to predict the water quality given weather data, I would ultimately want to publish the
result of the real-time regression model as a web service.

## Reasons for bad water quality

There are some reasons given by the
[Helsinki outdoor website](https://www.hel.fi/fi/kulttuuri-ja-vapaa-aika/ulkoilu-puistot-ja-luontokohteet/uimarannat/uimaveden-laatu-ja-sinilevat).
The biggest reason for the pollution of the water during heavy rain seems to be wastewater overflows (hulevesi).
And because Pikkukoski is at the downstream of Vantaanjoki it is one of the most polluted of swimming beaches in Helsinki
as all the bacteria and unwanted materials are pouring to the water all along the river.

The definition of bad water quality given by Helsinki for inland is that one of these observations is true:
* The amount of intestinal enterococci is over 400pmy/100ml
* The amount of Escherichia coli is over 1000pmy/100ml

The thresholds for coasts are lower (200pmy/100ml and 500pmy/100ml respectively).

There exists a [qualitative analysis of the swim water profile for Pikkukoski here](https://www.hel.fi/static/ymk/uimavedet/uimavesiprofiili-pikkukoski.pdf).
It says that the definition for heavy rain is as such: 7mm/1h, 10mm/4h or 20mm/24h. However, it also describes how during
the summer of 2022 results show that even less heavy rain negatively affects the water quality (4.5mm/24h). Also heavy rain
upstream even a week before might affect the water quality.

## Data sources and analysis

The data for the water quality is in PDF and does not have exact information about the time of each measurement. The time resolution
only reported per day, so the time of the measurement within a day is unknown.

The measurement by Helsinki include the following data points: enterococci, E. coli, Blue-green algae, whether the quality is good or
bad and other observations. The other observations at least for years 2023 and 2024 thus far seem to be empty for Pikkukoski.

Here are the pdf links for [water quality in 2024](https://www.hel.fi/static/liitteet/kaupunkiymparisto/kulttuuri-ja-vapaa-aika/uimarannat/Uimavedenlaatu_2024.pdf),
[water quality in 2023](https://www.hel.fi/static/liitteet/kaupunkiymparisto/kulttuuri-ja-vapaa-aika/uimarannat/Uimavedenlaatu_2023.pdf),
[water quality in 2022](https://www.hel.fi/static/liitteet-2019/Kymp/kulttuuri-ja-vapaa-aika/Uimavedenlaatu_2022.pdf)
and [water quality in 2021](https://www.hel.fi/static/liitteet-2019/Kymp/kulttuuri-ja-vapaa-aika/Uimavedenlaatu_2021.pdf) in Helsinki.

I manually paste the measurements from the pdf to a text file and parse it via `transform_pikkukoski_txt.py` such that it can
easily be read to a dataframe with pandas.

Here is an example page of the water quality pdf
![Example of the pdf page of Pakila, Pikkukoski and Tapaninvainio water quality in 2023](pics/pdf_page_example.png)

The weather data is from [Ilmatieteenlaitos](https://www.ilmatieteenlaitos.fi/) using [this service](https://www.ilmatieteenlaitos.fi/havaintojen-lataus).
The data requires some processing to behave nicely so the loading for weather data is implemented in `read_weather_data.py`.
For now I only got the temperature and the rain amount with the shortest possible time window for the summer of 2023 and
2024.

There were some missing data points from Helsinki-Vantaa lentoasema weather observations. Those were both manually and programmatically corrected to
reflect the previous rain amount. The missing data points were at most for a duration of half an hour.

In the beginning I'm only looking at weather data from the Kumpula weather station which is the closest station to Pikkukoski,
but going forward I assume looking into all the stations near Vantaanjoki will be useful for the analysis as the rain situation
upstream will affect water quality downstream. It would be great to have historical rain radar information such that I could
have spatially more granular data for the estimate of the amount of rain as any rain along the river affects the results.

In `analysis.ipynb` I explore the relation of the rain and temperature compared to the different water quality measurements
we get from Pikkukoski.