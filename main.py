from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from services.spot_searching_page.description_service import generate_description
from services.spot_searching_page.location_weather_services import get_location_weather
from services.spot_searching_page.map_service import generate_map_all, generate_map_selected
from services.spot_searching_page.question_service import ask_question
from services.spot_searching_page.search_service import search_tourist_spots
from services.spot_searching_page.search_spot_with_cu_location import search_tourist_spots_with_current_location
from typing import List
from services.spot_searching_page.weather_service import get_weather_data
import logging
from models.models import AskQuestionRequest, MapRequest, PlaceDescriptionRequest, SearchRequest, TouristSpot, SearchRequest1
from fastapi.responses import HTMLResponse
import os
import glob
from services.auth.routes import router as auth_router
from services.auth.social_routes import router as social_router
from services.auth.media_routes import router as media_router




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

# Include authentication and social routes
app.include_router(auth_router)
app.include_router(social_router)
app.include_router(media_router)


# Define upload directory
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# File path handler functions
def levenshtein_distance(s1, s2):
    """Calculate the Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
        
    if len(s2) == 0:
        return len(s1)
        
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
        
    return previous_row[-1]

def similarity_score(original, candidate):
    """Calculate a similarity score between two filenames."""
    return levenshtein_distance(original, candidate)

def get_actual_file_path(base_path, requested_path):
    """Attempts to find the actual file path when there's a mismatch."""
    # Remove leading slash if present
    if requested_path.startswith('/'):
        requested_path = requested_path[1:]
        
    # Construct the full path
    full_path = os.path.join(base_path, requested_path)
    
    # Check if the exact file exists
    if os.path.exists(full_path):
        return full_path
        
    # If exact file doesn't exist, try to find a close match
    try:
        # Get the directory and filename
        directory, filename = os.path.split(full_path)
        
        # Check if directory exists
        if not os.path.exists(directory):
            logger.warning(f"Directory does not exist: {directory}")
            return None
            
        # Get the filename without extension and the extension
        name, ext = os.path.splitext(filename)
        
        # Try to find files with similar names in the directory
        pattern = os.path.join(directory, f"{name[:-1]}*{ext}")
        matching_files = glob.glob(pattern)
        
        if matching_files:
            # Sort by similarity to the original filename
            matching_files.sort(key=lambda x: similarity_score(filename, os.path.basename(x)))
            best_match = matching_files[0]
            
            logger.info(f"Found close match for {filename}: {os.path.basename(best_match)}")
            return best_match
            
        # If no match found with pattern, list all files in directory
        all_files = os.listdir(directory)
        
        # Filter files with the same extension
        same_ext_files = [f for f in all_files if f.endswith(ext)]
        
        if same_ext_files:
            # Sort by similarity to the original filename
            same_ext_files.sort(key=lambda x: similarity_score(filename, x))
            best_match = os.path.join(directory, same_ext_files[0])
            
            logger.info(f"Found alternative match for {filename}: {os.path.basename(best_match)}")
            return best_match
            
        logger.warning(f"No matching file found for {filename} in {directory}")
        return None
        
    except Exception as e:
        logger.error(f"Error finding file match: {str(e)}")
        return None

# Custom StaticFiles class to handle file path mismatches
class CustomStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope) -> Response:
        try:
            # First try the standard StaticFiles lookup
            return await super().get_response(path, scope)
        except Exception as e:
            # If standard lookup fails, try to find a close match
            logger.info(f"Standard file lookup failed for {path}, trying to find close match")
            actual_path = get_actual_file_path(self.directory, path)
            
            if actual_path and os.path.exists(actual_path):
                # If we found a match, serve that file instead
                logger.info(f"Found alternative file: {actual_path}")
                return FileResponse(actual_path)
            
            # If no match found, re-raise the original exception
            logger.warning(f"No alternative file found for {path}")
            raise e

# Mount static files directory for uploads with custom handler
app.mount("/uploads", CustomStaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.get("/weather")
async def get_location_weather(lat: float, lon: float):
    weather_data = get_weather_data(lat, lon)
    if weather_data:
        return weather_data
    raise HTTPException(status_code=404, detail="Weather data unavailable")

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
    
# In your FastAPI backend code
@app.get("/search_with_current_location", response_model=List[TouristSpot])
async def search_tourist_spots_with_current_location_endpoint(lat: float, lon: float, radius: int = 10):
    try:
        # Create SearchRequest without 'location'
        request = SearchRequest1(lat=lat, lon=lon, radius=radius)
        spots = await search_tourist_spots_with_current_location(request)
        return spots
    except Exception as e:
        logger.error(f"Error searching tourist spots: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

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
    
    
# Run the app
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))  # Changed port to 8001 to avoid conflict
    uvicorn.run(app, host="0.0.0.0", port=port)
