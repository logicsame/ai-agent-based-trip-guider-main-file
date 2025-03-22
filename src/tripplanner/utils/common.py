import re
import json
from typing import List, Dict, Optional,Union
from pydantic import BaseModel



# Pydantic models
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


# Helper functions
def clean_json_string(json_str: str) -> str:
    json_str = re.sub(r'```(?:json)?\s*|\s*```', '', json_str)
    fixed_str = ''
    in_string = False
    escape_next = False
    
    for char in json_str:
        fixed_str += char
        
        if escape_next:
            escape_next = False
            continue
            
        if char == '\\':
            escape_next = True
        elif char == '"' and not escape_next:
            in_string = not in_string
    
    if in_string:
        fixed_str += '"'
    
    open_braces = fixed_str.count('{')
    close_braces = fixed_str.count('}')
    open_brackets = fixed_str.count('[')
    close_brackets = fixed_str.count(']')
    
    fixed_str += '}' * (open_braces - close_braces)
    fixed_str += ']' * (open_brackets - close_brackets)
    
    return fixed_str

def extract_and_parse_json(json_str: str) -> Dict:
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        cleaned_json = clean_json_string(json_str)
        try:
            return json.loads(cleaned_json)
        except json.JSONDecodeError:
            match = re.search(r'({.*})', json_str, re.DOTALL)
            if match:
                try:
                    extracted_json = match.group(1)
                    cleaned_extracted = clean_json_string(extracted_json)
                    return json.loads(cleaned_extracted)
                except json.JSONDecodeError:
                    raise
            else:
                raise