from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from services.spot_searching_page.description_service import generate_description
from services.spot_searching_page.location_weather_services import get_location_weather
from services.spot_searching_page.map_service import generate_map_all, generate_map_selected
from services.spot_searching_page.question_service import ask_question
from services.spot_searching_page.search_service import search_tourist_spots
from typing import List
from services.spot_searching_page.weather_service import get_weather_data
import logging
from models.models import AskQuestionRequest, MapRequest, PlaceDescriptionRequest, SearchRequest, TouristSpot
from fastapi.responses import HTMLResponse

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MainApp")

# Initialize FastAPI app
app = FastAPI()

# CORS middleware to allow frontend to communicate with the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import endpoints from services
@app.get("/weather")
async def get_location_weather(lat: float, lon: float):
    try:
        weather_data = await get_weather_data(lat, lon)
        if weather_data:
            return weather_data
        raise HTTPException(status_code=404, detail="Weather data unavailable")
    except Exception as e:
        logger.error(f"Error fetching weather data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch weather data")

@app.post("/map/all", response_class=HTMLResponse)
async def generate_map_all_endpoint(request: MapRequest):
    try:
        return await generate_map_all(request)
    except Exception as e:
        logger.error(f"Error generating map: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate map")

@app.post("/map/selected", response_class=HTMLResponse)
async def generate_map_selected_endpoint(spot: TouristSpot):
    try:
        return await generate_map_selected(spot)
    except Exception as e:
        logger.error(f"Error generating selected map: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate selected map")

@app.post("/search", response_model=List[TouristSpot])
@app.get("/search")
async def search_tourist_spots_endpoint(request: SearchRequest):
    try:
        return await search_tourist_spots(request)
    except Exception as e:
        logger.error(f"Error searching tourist spots: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search tourist spots")

@app.post("/generate_description", response_model=str)
async def generate_description_endpoint(request: PlaceDescriptionRequest):
    try:
        return await generate_description(request)
    except Exception as e:
        logger.error(f"Error generating description: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate description")

@app.post("/ask_question", response_model=str)
async def ask_question_endpoint(request: AskQuestionRequest):
    try:
        return await ask_question(request)
    except Exception as e:
        logger.error(f"Error answering question: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to answer question")