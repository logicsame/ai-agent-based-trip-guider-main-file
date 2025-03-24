import streamlit as st
import requests
import json
import folium
from streamlit_folium import folium_static
import pandas as pd
from geopy.geocoders import Nominatim
import urllib.parse
import time
from datetime import datetime
import plotly.express as px
from PIL import Image
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("GroqAPIManager")

# Set page configuration
st.set_page_config(
    page_title="Tourist Spot Finder",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define constants
BACKEND_URL = "https://ai-agent-based-trip-guider-main-production.up.railway.app/"  # Update with your actual backend URL
USER_AGENT = "TouristSpotFinder/1.0"

# Initialize session state variables if they don't exist
if 'tourist_spots' not in st.session_state:
    st.session_state.tourist_spots = []
if 'selected_spot' not in st.session_state:
    st.session_state.selected_spot = None
if 'spot_description' not in st.session_state:
    st.session_state.spot_description = ""
if 'weather_data' not in st.session_state:
    st.session_state.weather_data = None
if 'user_location' not in st.session_state:
    st.session_state.user_location = None
if 'question_history' not in st.session_state:
    st.session_state.question_history = []
if 'map_created' not in st.session_state:
    st.session_state.map_created = False
if 'last_search' not in st.session_state:
    st.session_state.last_search = {"location": "", "radius": 5}
if 'use_current_location' not in st.session_state:
    st.session_state.use_current_location = False

def get_user_location():
    """Get the user's current location based on IP address"""
    try:
        response = requests.get("https://ipinfo.io/json")
        if response.status_code == 200:
            data = response.json()
            if "loc" in data:
                lat, lon = map(float, data["loc"].split(","))
                city = data.get("city", "Unknown")
                region = data.get("region", "")
                country = data.get("country", "")
                location_name = f"{city}, {region}, {country}".strip().strip(",")
                return {"lat": lat, "lon": lon, "name": location_name}
    except Exception as e:
        st.error(f"Error getting location: {str(e)}")
    return None

def get_google_maps_direction_url(from_lat, from_lon, to_lat, to_lon):
    """Generate Google Maps directions URL"""
    base_url = "https://www.google.com/maps/dir/?api=1"
    origin = f"{from_lat},{from_lon}"
    destination = f"{to_lat},{to_lon}"
    url = f"{base_url}&origin={origin}&destination={destination}&travelmode=driving"
    return url

def get_google_search_url(query):
    """Generate Google search URL for a place"""
    encoded_query = urllib.parse.quote_plus(query)
    return f"https://www.google.com/search?q={encoded_query}"

def search_tourist_spots(location, radius):
    try:
        # Step 1: Get coordinates for the location using Nominatim
        nominatim_url = f"https://nominatim.openstreetmap.org/search?q={location}&format=json"
        response = requests.get(nominatim_url, headers={'User-Agent': USER_AGENT}, timeout=10)
        
        if response.status_code != 200:
            st.error(f"Failed to fetch coordinates: {response.status_code} - {response.text}")
            return [], None, None

        data = response.json()
        if not data:
            st.warning(f"No location found for '{location}'.")
            return [], None, None

        # Extract coordinates from Nominatim response
        center_lat = float(data[0]['lat'])
        center_lon = float(data[0]['lon'])
        
        # Step 2: Search for tourist spots using the backend API
        url = f"{BACKEND_URL}/search"
        payload = {"location": location, "radius": radius}
        
        with st.spinner(f"🔍 Searching for tourist spots near {location}..."):
            response = requests.post(url, json=payload, timeout=30)
            
        if response.status_code == 200:
            spots = response.json()
            if spots:
                st.session_state.tourist_spots = spots
                
                # Prepare map request payload
                map_payload = {
                    "spots": spots,
                    "center_lat": center_lat,
                    "center_lon": center_lon,
                    "radius": radius
                }
                
                # Get map from backend
                map_response = requests.post(f"{BACKEND_URL}/map/all", json=map_payload)
                
                if map_response.status_code == 200:
                    st.session_state.all_spots_map_html = map_response.text
                else:
                    st.error(f"Failed to fetch map: {map_response.status_code}")
                
                st.session_state.map_created = True
                st.session_state.last_search = {"location": location, "radius": radius}
                return spots, center_lat, center_lon
            else:
                st.warning(f"No tourist spots found near {location} within {radius} km radius.")
                return [], None, None
        else:
            error_msg = f"Error: {response.status_code}"
            try:
                error_data = response.json()
                if "detail" in error_data:
                    error_msg = error_data["detail"]
            except:
                pass
            st.error(f"Failed to search for tourist spots: {error_msg}")
            return [], None, None
    except Exception as e:
        st.error(f"Error connecting to backend: {str(e)}")
        return [], None, None

def search_tourist_spots_with_current_location(lat, lon, radius):
    """Search for tourist spots using current location coordinates"""
    try:
        url = f"{BACKEND_URL}/search_with_current_location"
        params = {
            "lat": lat,
            "lon": lon,
            "radius": radius
        }
        
        with st.spinner(f"🔍 Searching for tourist spots near your location..."):
            response = requests.get(url, params=params, timeout=30)
            
        if response.status_code == 200:
            spots = response.json()
            if spots:
                st.session_state.tourist_spots = spots
                
                # Prepare map request payload
                map_payload = {
                    "spots": spots,
                    "center_lat": lat,
                    "center_lon": lon,
                    "radius": radius
                }
                
                # Get map from backend
                map_response = requests.post(f"{BACKEND_URL}/map/all", json=map_payload)
                
                if map_response.status_code == 200:
                    st.session_state.all_spots_map_html = map_response.text
                else:
                    st.error(f"Failed to fetch map: {map_response.status_code}")
                
                st.session_state.map_created = True
                st.session_state.last_search = {"location": "Your Location", "radius": radius}
                return spots, lat, lon
            else:
                st.warning(f"No tourist spots found near your location within {radius} km radius.")
                return [], None, None
        else:
            error_msg = f"Error: {response.status_code}"
            try:
                error_data = response.json()
                if "detail" in error_data:
                    error_msg = error_data["detail"]
            except:
                pass
            st.error(f"Failed to search for tourist spots: {error_msg}")
            return [], None, None
    except Exception as e:
        st.error(f"Error connecting to backend: {str(e)}")
        return [], None, None

def get_weather_data(lat, lon):
    """Get weather data for a specific location"""
    try:
        url = f"{BACKEND_URL}/weather?lat={lat}&lon={lon}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error getting weather data: {str(e)}")
        return None

def generate_spot_description(spot, location, country, weather_data=None):
    """Generate a description for a selected tourist spot"""
    try:
        url = f"{BACKEND_URL}/generate_description"
        payload = {
            "spot_id": spot["id"],
            "spot_name": spot["name"],
            "spot_category": spot["category"],
            "location": location,
            "country": country,
            "weather_data": weather_data
        }
        
        with st.spinner("✨ Generating spot description..."):
            response = requests.post(url, json=payload)
            
        if response.status_code == 200:
            description = response.text.strip('"')  # Remove quotes if present
            st.session_state.spot_description = description
            return description
        else:
            error_msg = "Failed to generate description"
            try:
                error_data = response.json()
                if "detail" in error_data:
                    error_msg = error_data["detail"]
            except:
                pass
            st.error(f"{error_msg}")
            return None
    except Exception as e:
        st.error(f"Error generating description: {str(e)}")
        return None

def ask_question_about_spot(spot, location, country, question, weather_data=None):
    """Ask a question about a tourist spot"""
    try:
        url = f"{BACKEND_URL}/ask_question"
        payload = {
            "spot_id": spot["id"],
            "spot_name": spot["name"],
            "spot_category": spot["category"],
            "location": location,
            "country": country,
            "question": question,
            "weather_data": weather_data  # Ensure weather_data is included
        }
        
        # Debug: Log the payload
        logger.info(f"Payload sent to backend: {payload}")
        
        with st.spinner("🤔 Thinking about your question..."):
            response = requests.post(url, json=payload)
            
        if response.status_code == 200:
            answer = response.text.strip('"')  # Remove quotes if present
            # Add to question history
            st.session_state.question_history.append({
                "question": question,
                "answer": answer,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })
            return answer
        else:
            error_msg = "Failed to get an answer"
            try:
                error_data = response.json()
                if "detail" in error_data:
                    error_msg = error_data["detail"]
            except:
                pass
            st.error(f"{error_msg}")
            return None
    except Exception as e:
        st.error(f"Error asking question: {str(e)}")
        return None

def create_weather_widget(weather_data):
    """Create a visually appealing weather information widget"""
    if not weather_data:
        return st.info("Weather data not available")
    
    # Weather icons mapping
    weather_icons = {
        "clear sky": "☀️",
        "mainly clear": "🌤️",
        "partly cloudy": "⛅",
        "overcast": "☁️",
        "fog": "🌫️",
        "drizzle": "🌦️",
        "rain": "🌧️",
        "snow": "❄️",
        "thunderstorm": "⛈️"
    }
    
    # Find the best matching icon
    icon = "🌡️"  # Default
    for key in weather_icons:
        if key in weather_data["description"].lower():
            icon = weather_icons[key]
            break
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown(f"<h1 style='text-align: center; font-size: 4rem;'>{icon}</h1>", unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"<div style='font-size: 1.5rem; font-weight: bold;'>{weather_data['temperature']}°C</div>", unsafe_allow_html=True)
        st.markdown(f"<div>{weather_data['description'].title()}</div>", unsafe_allow_html=True)
        
        # Rain forecast
        if 'forecast' in weather_data:
            if weather_data['forecast']['day1']['rain_chance']:
                st.markdown("🌧️ **Rain expected in next 24h**")
            else:
                st.markdown("✅ **No rain expected in next 24h**")

def main():
    # # Custom CSS
    # st.markdown("""
    # <style>
    # .main-header {
    #     font-size: 2.5rem;
    #     font-weight: bold;
    #     color: #1f77b4;
    #     margin-bottom: 0.5rem;
    # }
    # .sub-header {
    #     font-size: 1.5rem;
    #     font-weight: bold;
    #     color: #1f77b4;
    #     margin: 1rem 0 0.5rem 0;
    # }
    # .info-text {
    #     color: #666;
    #     margin-bottom: 1rem;
    # }
    # .card {
    #     background-color: #f9f9f9;
    #     border-radius: 10px;
    #     padding: 1.5rem;
    #     box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    #     margin-bottom: 1rem;
    # }
    # .weather-box {
    #     background-color: #e6f3ff;
    #     border-radius: 10px;
    #     padding: 1rem;
    #     margin: 1rem 0;
    # }
    # .highlight-box {
    #     background-color: #f0f7ff;
    #     border-radius: 10px;
    #     padding: 1.5rem;
    #     margin: 1rem 0;
    # }
    # </style>
    # """, unsafe_allow_html=True)
    
    # Header
    st.markdown("<div class='main-header'>🗺️ Tourist Spot Finder</div>", unsafe_allow_html=True)
    st.markdown("<div class='info-text'>Discover amazing places around you, get detailed descriptions, weather information, and directions.</div>", unsafe_allow_html=True)
    
    # Get user's location if not already obtained
    if not st.session_state.user_location:
        st.session_state.user_location = get_user_location()
    
    # Search section
    st.markdown("<div class='sub-header'>🔍 Find Places</div>", unsafe_allow_html=True)
    
    # Toggle for current location
    use_current_location = st.checkbox("Use my current location", value=st.session_state.use_current_location)
    st.session_state.use_current_location = use_current_location
    
    if use_current_location:
        if st.session_state.user_location:
            st.info(f"Using your current location: {st.session_state.user_location.get('name', 'Unknown')}")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                radius = st.number_input(
                    "Search Radius (km)", 
                    min_value=1, 
                    max_value=50, 
                    value=max(1, st.session_state.last_search.get("radius", 5)),
                    step=1
                )
            
            with col2:
                search_button = st.button("🔍 Search Places Near Me", use_container_width=True)
            
            if search_button:
                spots, center_lat, center_lon = search_tourist_spots_with_current_location(
                    st.session_state.user_location["lat"],
                    st.session_state.user_location["lon"],
                    radius
                )
                if spots and center_lat and center_lon:
                    st.success(f"Found {len(spots)} tourist spots near your location")
        else:
            st.warning("Could not determine your current location. Please enable location services or enter a location manually.")
    else:
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            location = st.text_input(
                "Location", 
                value=st.session_state.last_search.get("location", st.session_state.user_location.get("name", "") if st.session_state.user_location else ""),
                placeholder="Enter city, landmark, or region"
            )
        
        with col2:
            radius = st.number_input(
                "Search Radius (km)", 
                min_value=1, 
                max_value=50, 
                value=max(1, st.session_state.last_search.get("radius", 5)),
                step=1
            )
        
        with col3:
            search_button = st.button("🔍 Search Places", use_container_width=True)
        
        if search_button and location:
            spots, center_lat, center_lon = search_tourist_spots(location, radius)
            if spots and center_lat and center_lon:
                st.success(f"Found {len(spots)} tourist spots near {location}")

    if st.session_state.tourist_spots:
        # Display the map from backend
        st.markdown("<div class='sub-header'>📍 All Tourist Spots</div>", unsafe_allow_html=True)
        if 'all_spots_map_html' in st.session_state and st.session_state.all_spots_map_html:
            st.components.v1.html(st.session_state.all_spots_map_html, width=1150, height=500)
        else:
            st.warning("Map not available")

        # Convert spot list to DataFrame for easier filtering and display
        spots_df = pd.DataFrame(st.session_state.tourist_spots)
    
        # Add category filter
        categories = ["All Categories"] + sorted(spots_df["category"].unique().tolist())
        selected_category = st.selectbox("Filter by Category", categories)
    
        if selected_category != "All Categories":
            filtered_spots = spots_df[spots_df["category"] == selected_category]
        else:
            filtered_spots = spots_df
    
        # Display the filtered spots
        if filtered_spots.shape[0] > 0:
            # Spot selection dropdown
            st.markdown("<div class='sub-header'>✨ Select a Tourist Spot</div>", unsafe_allow_html=True)
            spot_options = [f"{spot['name']} ({spot['category']})" for spot in filtered_spots.to_dict("records")]
    
            selected_option = st.selectbox("Choose a place to get more information", spot_options, key="spot_selector")
            selected_index = spot_options.index(selected_option)
            selected_spot = filtered_spots.iloc[selected_index].to_dict()
    
            # Ensure selected_spot is initialized as an empty dictionary if it doesn't exist or is None
            if 'selected_spot' not in st.session_state or st.session_state.selected_spot is None:
                st.session_state.selected_spot = {}
    
            # Store selected spot in session state if it has changed
            if not st.session_state.selected_spot or st.session_state.selected_spot.get("id") != selected_spot.get("id"):
                st.session_state.selected_spot = selected_spot
                st.session_state.spot_description = ""  # Clear the previous description
    
            # Get weather data for the selected spot
            weather_data = get_weather_data(selected_spot["lat"], selected_spot["lon"])
            st.session_state.weather_data = weather_data
    
            # Create two columns for info and map
            col1, col2 = st.columns([1, 1])
    
            with col1:
                st.markdown(f"<div class='card'>", unsafe_allow_html=True)
                st.markdown(f"<h2>{selected_spot['name']}</h2>", unsafe_allow_html=True)
                st.markdown(f"<p><strong>Category:</strong> {selected_spot['category'].replace('_', ' ').title()}</p>", unsafe_allow_html=True)
        
                # Extract location info
                if st.session_state.use_current_location:
                    location_name = "Your Location"
                    country = st.session_state.user_location.get("name", "Unknown").split(",")[-1].strip()
                else:
                    location_parts = st.session_state.last_search["location"].split(",")
                    location_name = location_parts[0].strip() if location_parts else "Unknown"
                    country = location_parts[-1].strip() if len(location_parts) > 1 else "Unknown"
        
                # Generate description if not already generated for this spot
                if not st.session_state.spot_description:
                    description = generate_spot_description(selected_spot, location_name, country, weather_data)
                else:
                    description = st.session_state.spot_description
        
                if description:
                    st.markdown(f"<p>{description}</p>", unsafe_allow_html=True)
        
                # Weather information
                if weather_data:
                    st.markdown("<div class='weather-box'>", unsafe_allow_html=True)
                    st.markdown("<h3>Current Weather</h3>", unsafe_allow_html=True)
                    create_weather_widget(weather_data)
                    st.markdown("</div>", unsafe_allow_html=True)
        
                # Links for Google Maps directions and search
                if st.session_state.user_location:
                    directions_url = get_google_maps_direction_url(
                        st.session_state.user_location["lat"],
                        st.session_state.user_location["lon"],
                        selected_spot["lat"],
                        selected_spot["lon"]
                    )
                    st.markdown(f"[🧭 Get Directions on Google Maps]({directions_url})")
        
                search_url = get_google_search_url(f"{selected_spot['name']} {location_name}")
                st.markdown(f"[🔍 Search on Google]({search_url})")
        
                st.markdown("</div>", unsafe_allow_html=True)
    
            with col2:
                # Fetch and display the selected spot's map from the backend
                try:
                    map_response = requests.post(f"{BACKEND_URL}/map/selected", json=selected_spot)
                    if map_response.status_code == 200:
                        st.components.v1.html(map_response.text, width=550, height=400)
                    else:
                        st.warning("Map not available for this spot")
                except Exception as e:
                    st.error(f"Error fetching map: {str(e)}")
        
            # Ask a question section
            st.markdown("<div class='sub-header'>❓ Ask About This Place</div>", unsafe_allow_html=True)
            st.markdown("<p class='info-text'>Ask anything about this place, activities, best time to visit, or weather conditions.</p>", unsafe_allow_html=True)
        
            # Suggestion chips
            suggestion_cols = st.columns(4)
            suggestions = [
                "What is the best time to visit?",
                "Any chances of rain today?",
                "What activities can I do here?",
                "Is this place family-friendly?"
            ]
        
            selected_suggestion = None
            for i, suggestion in enumerate(suggestions):
                with suggestion_cols[i]:
                    if st.button(suggestion, key=f"sugg_{i}"):
                        selected_suggestion = suggestion
        
            # Question input
            user_question = st.text_input("Your question", value=selected_suggestion if selected_suggestion else "", placeholder="E.g., What is the best time to visit?")
        
            if st.button("📝 Ask Question", use_container_width=True) and user_question:
                answer = ask_question_about_spot(selected_spot, location_name, country, user_question, weather_data)
                if answer:
                    st.markdown("<div class='highlight-box'>", unsafe_allow_html=True)
                    st.markdown(f"<p><strong>Q:</strong> {user_question}</p>", unsafe_allow_html=True)
                    st.markdown(f"<p><strong>A:</strong> {answer}</p>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
        
            # Question history
            if st.session_state.question_history:
                with st.expander("Previous Questions & Answers", expanded=False):
                    for item in reversed(st.session_state.question_history[-5:]):
                        st.markdown(f"<p><strong>Q:</strong> {item['question']}</p>", unsafe_allow_html=True)
                        st.markdown(f"<p><strong>A:</strong> {item['answer']}</p>", unsafe_allow_html=True)
                        st.markdown(f"<p><small>Asked at {item['timestamp']}</small></p>", unsafe_allow_html=True)
                        st.markdown("<hr>", unsafe_allow_html=True)
        else:
            st.warning("No places found with the selected filter. Try a different category.")
    else:
        # Show welcome message and instructions if no search has been performed yet
        st.markdown("<div class='highlight-box'>", unsafe_allow_html=True)
        st.markdown("### 👋 Welcome to Tourist Spot Finder!")
        st.markdown("""
        Discover interesting places around any location:
        1. Choose to use your current location or enter a location manually
        2. Set your preferred search radius (in kilometers)
        3. Click "Search Places" to find tourist spots
        4. Select a spot to get detailed information and directions
        5. Ask questions about the selected place
        """)
        st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: gray;'>© 2025 Tourist Spot Finder | Created with Streamlit</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()