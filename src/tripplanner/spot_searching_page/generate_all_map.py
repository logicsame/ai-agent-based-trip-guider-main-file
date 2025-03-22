import fastapi
from fastapi import FastAPI, HTTPException, Query, Depends
from tripplanner.utils.common import MapRequest
from fastapi.responses import HTMLResponse
import folium


app = FastAPI()

@app.post("/map/all", response_class=HTMLResponse)
async def generate_map_all(request: MapRequest):
    spots = request.spots
    if not spots:
        raise HTTPException(status_code=404, detail="No tourist spots found to generate a map.")
    
    # Create map centered on search location
    m = folium.Map(location=[request.center_lat, request.center_lon], zoom_start=12)
    
    # Add circle for search radius
    folium.Circle(
        location=[request.center_lat, request.center_lon],
        radius=request.radius * 1000,  # Convert km to meters
        color="#3186cc",
        fill=True,
        fill_color="#3186cc",
        fill_opacity=0.2,
        weight=2,
        opacity=0.8
    ).add_to(m)
    
    # Category color and icon mapping
    category_config = {
        "attraction": {"color": "red", "icon": "star"},
        "museum": {"color": "blue", "icon": "university"},
        "park": {"color": "green", "icon": "tree"},
        "viewpoint": {"color": "orange", "icon": "binoculars"},
        "hotel": {"color": "purple", "icon": "bed"},
        "restaurant": {"color": "cadetblue", "icon": "cutlery"},
        "historic": {"color": "darkred", "icon": "landmark"},
        "beach": {"color": "lightblue", "icon": "umbrella-beach"},
        "nature": {"color": "darkgreen", "icon": "leaf"},
        "waterfall": {"color": "lightred", "icon": "water"},
        "forest": {"color": "green", "icon": "tree"},
        "default": {"color": "gray", "icon": "info-circle"}
    }
    
    # Add markers with category-based colors and icons
    for spot in spots:
        # Get category from spot data
        category = spot.category.lower().split("_")[0]
        config = category_config.get(category, category_config["default"])
        
        folium.Marker(
            location=[spot.lat, spot.lon],
            popup=f"<b>{spot.name}</b><br>{spot.category}",
            tooltip=spot.name,
            icon=folium.Icon(
                color=config["color"],  # Marker color
                icon=config["icon"],    # Font Awesome icon
                prefix="fa"            # Use Font Awesome icons
            )
        ).add_to(m)
    
    return m._repr_html_()