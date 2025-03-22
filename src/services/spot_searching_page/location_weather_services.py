

from fastapi import FastAPI, HTTPException, Query, Depends
from services.spot_searching_page import weather_service


async def get_location_weather(lat: float, lon: float):
    weather_data = weather_service(lat, lon)
    if weather_data:
        return weather_data
    raise HTTPException(status_code=404, detail="Weather data unavailable")