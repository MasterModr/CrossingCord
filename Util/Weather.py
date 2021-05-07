from var_secrets import *
from Util.Timer import setInterval
from datetime import datetime
import pytz

import requests


def get_weather():
    url = "http://api.openweathermap.org/data/2.5/weather?"
    city = "Montreal"

    complete_url = url + "appid=" + WEATHER_API_KEY + "&q=" + city

    response = requests.get(complete_url)

    x = response.json()

    # Now x contains list of nested dictionaries
    # Check the value of "cod" key is equal to
    # "404", means city is found otherwise,
    # city is not found

    if x["cod"] != "404":

        print(x["weather"])
        d = datetime.now()
        timezone = pytz.timezone("America/New_York")
        d = timezone.localize(d)
        weather = {

            'id': x["weather"][0]["id"],
            'icon': x["weather"][0]["icon"],
            'description': x["weather"][0]["description"],
            'time': d.strftime("%H:%M")

            }
        return weather
    else:
        return None
