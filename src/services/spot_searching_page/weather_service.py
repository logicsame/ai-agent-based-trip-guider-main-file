import logging
import requests
import time
from typing import Optional, NamedTuple, Dict, Any
from models.models import WeatherData


# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("GroqAPIManager")



def get_weather_data(lat: float, lon: float, max_retries: int = 3, retry_delay: int = 2) -> Optional[WeatherData]:
    retries = 0
    while retries < max_retries:
        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code&hourly=precipitation,weather_code&forecast_days=3"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                weather_codes = {
                    0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
                    45: "fog", 48: "depositing rime fog", 51: "light drizzle", 53: "moderate drizzle",
                    55: "dense drizzle", 56: "light freezing drizzle", 57: "dense freezing drizzle",
                    61: "slight rain", 63: "moderate rain", 65: "heavy rain",
                    66: "light freezing rain", 67: "heavy freezing rain", 71: "slight snow fall",
                    73: "moderate snow fall", 75: "heavy snow fall", 77: "snow grains",
                    80: "slight rain showers", 81: "moderate rain showers", 82: "violent rain showers",
                    85: "slight snow showers", 86: "heavy snow showers", 95: "thunderstorm",
                    96: "thunderstorm with slight hail", 99: "thunderstorm with heavy hail"
                }
                weather_code = data['current']['weather_code']
                next_48h_precip = data['hourly']['precipitation'][:48]
                hourly_weather_codes = data['hourly']['weather_code'][:48]
                
                day1_precip = next_48h_precip[:24]
                day2_precip = next_48h_precip[24:48]
                
                day1_weather_codes = hourly_weather_codes[:24]
                day2_weather_codes = hourly_weather_codes[24:48]
            
                rain_weather_codes = [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99]
                
                day1_rain_chance = any(p > 0.1 for p in day1_precip)
                day1_rain_hours = sum(1 for p in day1_precip if p > 0.1)
                day1_has_rain_codes = any(code in rain_weather_codes for code in day1_weather_codes)
                
                day2_rain_chance = any(p > 0.1 for p in day2_precip)
                day2_rain_hours = sum(1 for p in day2_precip if p > 0.1)
                day2_has_rain_codes = any(code in rain_weather_codes for code in day2_weather_codes)
            
                forecast_data = {
                    'next_48h': {
                        'rain_chance': any(p > 0.1 for p in next_48h_precip) or any(code in rain_weather_codes for code in hourly_weather_codes),
                        'rain_hours': sum(1 for p in next_48h_precip if p > 0.1),
                        'max_precipitation': float(max(next_48h_precip)) if next_48h_precip else 0.0,
                    },
                    'day1': {
                        'rain_chance': day1_rain_chance or day1_has_rain_codes,
                        'rain_hours': day1_rain_hours,
                        'max_precipitation': float(max(day1_precip)) if day1_precip else 0.0,
                    },
                    'day2': {
                        'rain_chance': day2_rain_chance or day2_has_rain_codes,
                        'rain_hours': day2_rain_hours,
                        'max_precipitation': float(max(day2_precip)) if day2_precip else 0.0,
                    }
                }
            
                return WeatherData(
                    temperature=data['current']['temperature_2m'],
                    description=weather_codes.get(weather_code, "unknown weather"),
                    forecast=forecast_data
                )
            else:
                logger.warning(f"Weather API returned status code {response.status_code}: {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            retries += 1
            logger.warning(f"Attempt {retries} failed: {str(e)}")
            if retries < max_retries:
                time.sleep(retry_delay * retries)  # Exponential backoff
            else:
                logger.error(f"Failed to fetch weather data after {max_retries} attempts: {str(e)}")
                return None
    return None