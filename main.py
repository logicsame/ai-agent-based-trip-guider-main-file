from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from services.weather_service import get_weather_data
from services.map_service import generate_map_all, generate_map_selected
from services.search_service import search_tourist_spots
from services.description_service import generate_description
from services.question_service import ask_question
from models import SearchRequest, MapRequest, PlaceDescriptionRequest, AskQuestionRequest, TouristSpot
from fastapi.responses import HTMLResponse
import logging

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
    weather_data = get_weather_data(lat, lon)
    if weather_data:
        return weather_data
    raise HTTPException(status_code=404, detail="Weather data unavailable")

@app.post("/map/all", response_class=HTMLResponse)
async def generate_map_all_endpoint(request: MapRequest):
    return generate_map_all(request)

@app.post("/map/selected", response_class=HTMLResponse)
async def generate_map_selected_endpoint(spot: TouristSpot):
    return generate_map_selected(spot)

@app.post("/search", response_model=List[TouristSpot])
@app.get("/search")
async def search_tourist_spots_endpoint(request: SearchRequest):
    return search_tourist_spots(request)

@app.post("/generate_description", response_model=str)
async def generate_description_endpoint(request: PlaceDescriptionRequest):
    return generate_description(request)

@app.post("/ask_question", response_model=str)
async def ask_question_endpoint(request: AskQuestionRequest):
    return ask_question(request)

# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)