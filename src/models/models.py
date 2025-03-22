# Pydantic models
from typing import Dict, List, Optional, Union
from pydantic import BaseModel


class SearchRequest(BaseModel):
    location: str
    radius: int = 5  # Default to 5km

class TouristSpot(BaseModel):
    id: str
    name: str
    category: str
    lat: float
    lon: float
    description: Optional[str] = None
    tags: Dict[str, str]

class WeatherData(BaseModel):
    temperature: float
    description: str
    forecast: Dict[str, Dict[str, Union[bool, float, int]]]

class PlaceDescriptionRequest(BaseModel):
    spot_id: str
    spot_name: str
    spot_category: str
    location: str
    country: str
    weather_data: Optional[WeatherData] = None


class AskQuestionRequest(BaseModel):
    spot_id: str
    spot_name: str
    spot_category: str
    location: str
    country: str
    question: str
    weather_data: Optional[WeatherData] = None


class MapRequest(BaseModel):
    spots: List[TouristSpot]
    center_lat: float
    center_lon: float
    radius: int