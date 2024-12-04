import openmeteo_requests
import requests

import requests_cache
import pandas as pd
from retry_requests import retry

from flask import Flask, jsonify

app = Flask(__name__)

def check_bad_weather(current_temperature_2m, current_apparent_temperature, first_precipitation_value,
                      current_wind_speed_10m):
    # Проверяем условия неблагоприятной погоды
    if (current_temperature_2m < 5 or current_temperature_2m > 28 or
            current_apparent_temperature < -5 or current_apparent_temperature > 30 or
            first_precipitation_value > 60 or
            current_wind_speed_10m > 7):
        return False, 'Ой-ой, погода плохая'
    else:
        return True, 'Погода — супер'

cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)
url = "https://api.open-meteo.com/v1/forecast"

params = {
	"latitude": 34.0522,
	"longitude": -118.2437,
	"current": ["temperature_2m", "relative_humidity_2m", "apparent_temperature", "wind_speed_10m"],
	"daily": "precipitation_probability_max",
	"timezone": "Europe/Moscow",
	"forecast_days": 1
}
responses = openmeteo.weather_api(url, params=params)
response = responses[0]
current = response.Current()
current_temperature_2m = current.Variables(0).Value()
current_relative_humidity_2m = current.Variables(1).Value()
current_apparent_temperature = current.Variables(2).Value()
current_wind_speed_10m = current.Variables(3).Value()

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
#print(daily_dataframe)


@app.route('/check_weather', methods=['GET'])
def weather_check():
    result, message = check_bad_weather(current_temperature_2m, current_apparent_temperature,
                                        first_precipitation_value, current_wind_speed_10m)

    return message

if __name__ == '__main__':
    app.run(debug=True)