

from fastapi import FastAPI, HTTPException, Query, Depends
from services.spot_searching_page import get_weather_data


async def get_location_weather(lat: float, lon: float):
    weather_data = get_weather_data(lat, lon)
    if weather_data:
        return weather_data
    raise HTTPException(status_code=404, detail="Weather data unavailable")