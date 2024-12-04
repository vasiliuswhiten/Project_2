import openmeteo_requests

import requests_cache
import pandas as pd
from retry_requests import retry

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below
url = "https://api.open-meteo.com/v1/forecast"
params = {
	"latitude": 55.7522,
	"longitude": 37.6156,
	"current": ["temperature_2m", "relative_humidity_2m", "apparent_temperature", "cloud_cover", "wind_speed_10m"],
	"daily": "precipitation_probability_max",
	"timezone": "Europe/Moscow",
	"forecast_days": 3
}
responses = openmeteo.weather_api(url, params=params)

# Process first location. Add a for-loop for multiple locations or weather models
response = responses[0]
print(f"Координаты {response.Latitude()}°N {response.Longitude()}°E")

# Current values. The order of variables needs to be the same as requested.
current = response.Current()
current_temperature_2m = current.Variables(0).Value()
current_relative_humidity_2m = current.Variables(1).Value()
current_apparent_temperature = current.Variables(2).Value()
current_cloud_cover = current.Variables(3).Value()
current_wind_speed_10m = current.Variables(4).Value()

print(f"Температура {round(current_temperature_2m, 2)}°C (ощущается как {round(current_apparent_temperature)}°C)")
print(f"Влажность {current_relative_humidity_2m}%")
print(f"Скорость ветра {round(current_wind_speed_10m, 2)}м/с")

# Process daily data. The order of variables needs to be the same as requested.
daily = response.Daily()
daily_precipitation_probability_max = daily.Variables(0).ValuesAsNumpy()

daily_data = {"date": pd.date_range(
	start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
	end = pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
	freq = pd.Timedelta(seconds = daily.Interval()),
	inclusive = "left"
)}
daily_data["precipitation_probability_max"] = daily_precipitation_probability_max

daily_dataframe = pd.DataFrame(data = daily_data)
first_precipitation_value = daily_dataframe["precipitation_probability_max"].iloc[0]
print(f"Вероятность осадков {first_precipitation_value}%")