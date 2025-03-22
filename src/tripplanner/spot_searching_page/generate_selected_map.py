import fastapi
from fastapi import FastAPI, HTTPException, Query, Depends
from tripplanner.utils.common import TouristSpot
from fastapi.responses import HTMLResponse
import folium

app = FastAPI()

# Endpoint: Generate Map of a Selected Place
@app.post("/map/selected", response_class=HTMLResponse)
async def generate_map_selected(spot: TouristSpot):
    # Create a map centered on the selected spot
    m = folium.Map(location=[spot.lat, spot.lon], zoom_start=15)
    
    # Add a marker for the selected spot
    folium.Marker(
        location=[spot.lat, spot.lon],
        popup=f"<b>{spot.name}</b><br>{spot.category}",
        tooltip=spot.name
    ).add_to(m)
    
    # Return the map as HTML
    return m._repr_html_()