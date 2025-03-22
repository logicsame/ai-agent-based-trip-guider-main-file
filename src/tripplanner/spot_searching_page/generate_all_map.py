import fastapi
from fastapi import FastAPI, HTTPException, Query, Depends
from tripplanner.utils.common import MapRequest
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.post("/map/all", response_class=HTMLResponse)
async def generate_map_all(request: MapRequest):
    spots = request.spots
    if not spots:
        raise HTTPException(status_code=404, detail="No tourist spots found to generate a map.")