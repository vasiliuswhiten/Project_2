from flask import Flask

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

@app.route('/check_weather', methods=['GET'])
def weather_check():
    try:
        current_temperature_2m = float(input("Введите текущую температуру(°C): "))
        current_apparent_temperature = float(input("Введите текущую ощущаемую температуру (°C): "))
        first_precipitation_value = float(input("Введите вероятность осадков (%): "))
        current_wind_speed_10m = float(input("Введите скорость ветра (м/с): "))

        result, message = check_bad_weather(current_temperature_2m, current_apparent_temperature,
                                                 first_precipitation_value, current_wind_speed_10m)

        print(message)

    except ValueError:
        print("Пожалуйста, введите корректные числовые значения.")

    return message

if __name__ == '__main__':
    app.run(debug=True)