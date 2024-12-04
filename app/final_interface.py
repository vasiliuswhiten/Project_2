import openmeteo_requests
import requests
import requests_cache
import pandas as pd
from retry_requests import retry
from flask import Flask, render_template, request

app = Flask(__name__)


# Проверка параметров погоды на благоприятность
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


# Технические параметры для API
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)


# Страница ввода городов
@app.route('/')
def index():
    return render_template('index.html')


# Получение координат по городу и запись в переменные
def get_coordinates(city_name):
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1&language=ru&format=json"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Проверка на ошибки HTTP
        data = response.json()

        if "results" in data and len(data["results"]) > 0:
            latitude = data["results"][0]["latitude"]
            longitude = data["results"][0]["longitude"]
            return latitude, longitude
        else:
            raise ValueError(f"Не удалось найти координаты для города: {city_name}")

    except requests.exceptions.RequestException:
        raise ConnectionError("Ошибка подключения к серверу.")
    except ValueError as ve:
        raise ve


# Получение данных о погоде по координатам
def get_weather_data(latitude, longitude):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ["temperature_2m", "relative_humidity_2m", "apparent_temperature", "wind_speed_10m"],
        "daily": "precipitation_probability_max",
        "timezone": "Europe/Moscow",
        "forecast_days": 1
    }

    try:
        responses = openmeteo.weather_api(url, params=params)

        if responses:
            response = responses[0]
            current = response.Current()
            current_temperature_2m = current.Variables(0).Value()
            current_relative_humidity_2m = current.Variables(1).Value()
            current_apparent_temperature = current.Variables(2).Value()
            current_wind_speed_10m = current.Variables(3).Value()

            daily = response.Daily()
            daily_precipitation_probability_max = daily.Variables(0).ValuesAsNumpy()

            daily_data = {
                "precipitation_probability_max": daily_precipitation_probability_max,
            }

            daily_dataframe = pd.DataFrame(data=daily_data)
            first_precipitation_value = daily_dataframe["precipitation_probability_max"].iloc[0]

            return (current_temperature_2m, current_apparent_temperature,
                    first_precipitation_value, current_wind_speed_10m)

    except Exception as e:
        raise ConnectionError("Ошибка получения данных о погоде.")


# Обработка данных после отправки формы
@app.route('/submit', methods=['POST'])
def submit():
    departure_place = request.form['departure_place']
    destination_place = request.form['destination_place']

    try:
        # Координаты отправной точки
        latitude1, longitude1 = get_coordinates(departure_place)
        # Погода в отправной точке
        departure_weather_data = get_weather_data(latitude1, longitude1)
        # Координаты конечной точки
        latitude2, longitude2 = get_coordinates(destination_place)
        # Погода в конечной точке
        destination_weather_data = get_weather_data(latitude2, longitude2)
        # Проверка погоды на благоприятность для обеих точек
        departure_weather_check_result, departure_weather_message = check_bad_weather(*departure_weather_data)
        destination_weather_check_result, destination_weather_message = check_bad_weather(*destination_weather_data)

        if departure_weather_check_result and destination_weather_check_result:
            overall_message = 'Погода хорошая в обеих точках!'
        elif not(departure_weather_check_result) and not(destination_weather_check_result):
            overall_message = 'Ой-ой, погода везде плохая'
        else:
            overall_message = f'{departure_weather_message} в отправной точке и {destination_weather_message} в конечной точке.'

        return f"{overall_message}"

    except ValueError as ve:
        return str(ve)  # Возвращаем сообщение об ошибке пользователю
    except ConnectionError as ce:
        return str(ce)  # Возвращаем сообщение об ошибке подключения пользователю
    except Exception as e:
        return "Упс. Произошла непредвиденная ошибка. Пожалуйста, попробуйте снова."


if __name__ == '__main__':
    app.run(debug=True)



