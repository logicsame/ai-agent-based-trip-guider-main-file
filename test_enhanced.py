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
from services.auth.social_interface import SocialMediaInterface
from services.auth.post_viewing_interface import PostViewingInterface

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
BACKEND_URL = "http://127.0.0.1:8000/"  # Update with your actual backend URL
USER_AGENT = "TouristSpotFinder/1.0"

# Initialize social media interface
social_interface = SocialMediaInterface(backend_url=BACKEND_URL)
post_viewing_interface = PostViewingInterface(social_interface, backend_url=BACKEND_URL)

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
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "info"
if 'navigate_to_spot' not in st.session_state:
    st.session_state.navigate_to_spot = None
if 'navigate_to_post' not in st.session_state:
    st.session_state.navigate_to_post = None

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
    # Custom CSS for better UI
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin: 1rem 0 0.5rem 0;
    }
    .info-text {
        color: #666;
        margin-bottom: 1rem;
    }
    .card {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .weather-box {
        background-color: #e6f3ff;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .highlight-box {
        background-color: #f0f7ff;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .post-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        border-left: 4px solid #1f77b4;
    }
    .comment-card {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 0.8rem;
        margin: 0.5rem 0;
        border-left: 3px solid #aec7e8;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Render authentication UI in sidebar
    social_interface.render_auth_ui()
    
    # Header
    st.markdown("<div class='main-header'>🗺️ Tourist Spot Finder</div>", unsafe_allow_html=True)
    st.markdown("<div class='info-text'>Discover amazing places around you, get detailed descriptions, weather information, and directions.</div>", unsafe_allow_html=True)
    
    # Check if we need to navigate to a specific spot (from trending posts)
    if st.session_state.navigate_to_spot:
        # Find the spot in the tourist spots list
        for spot in st.session_state.tourist_spots:
            if spot["id"] == st.session_state.navigate_to_spot:
                st.session_state.selected_spot = spot
                
                # Get weather data for the spot
                weather_data = get_weather_data(spot["lat"], spot["lon"])
                st.session_state.weather_data = weather_data
                
                # Generate description
                location = st.session_state.last_search.get("location", "")
                country = location.split(",")[-1].strip() if "," in location else location
                generate_spot_description(spot, location, country, weather_data)
                
                # Set active tab to social
                st.session_state.active_tab = "social"
                
                # Clear navigation flags
                navigate_to_post = st.session_state.navigate_to_post
                st.session_state.navigate_to_spot = None
                st.session_state.navigate_to_post = None
                
                # Rerun to update UI
                st.rerun()
    
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
            search_button = st.button("🔍 Search", use_container_width=True)
        
        if search_button and location:
            spots, center_lat, center_lon = search_tourist_spots(location, radius)
            if spots and center_lat and center_lon:
                st.success(f"Found {len(spots)} tourist spots near {location}")
    
    # Display trending posts only if explicitly requested (not automatically after login)
    # Add a toggle for showing trending experiences
    if st.session_state.is_authenticated and not st.session_state.selected_spot:
        show_trending = st.checkbox("Show trending experiences", value=False, key="show_trending_toggle")
        if show_trending:
            st.markdown("<div class='sub-header'>🔥 Trending Experiences</div>", unsafe_allow_html=True)
            post_viewing_interface.render_trending_posts(limit=3)
    
    # Display map if available
    if st.session_state.map_created and hasattr(st.session_state, 'all_spots_map_html'):
        st.markdown("<div class='sub-header'>🗺️ Map View</div>", unsafe_allow_html=True)
        st.components.v1.html(st.session_state.all_spots_map_html, height=400)
    
    # Display tourist spots
    if st.session_state.tourist_spots:
        st.markdown("<div class='sub-header'>📍 Tourist Spots</div>", unsafe_allow_html=True)
        
        # Create a grid of cards for tourist spots
        cols = st.columns(3)
        for i, spot in enumerate(st.session_state.tourist_spots):
            with cols[i % 3]:
                with st.container():
                    st.markdown(f"<div class='card'>", unsafe_allow_html=True)
                    st.markdown(f"### {spot['name']}")
                    st.markdown(f"**Category:** {spot['category']}")
                    
                    # Button to view details
                    if st.button(f"View Details", key=f"view_{spot['id']}"):
                        st.session_state.selected_spot = spot
                        
                        # Get weather data for the spot
                        weather_data = get_weather_data(spot["lat"], spot["lon"])
                        st.session_state.weather_data = weather_data
                        
                        # Generate description if not already generated
                        if not st.session_state.spot_description or st.session_state.selected_spot["id"] != spot["id"]:
                            location = st.session_state.last_search.get("location", "")
                            country = location.split(",")[-1].strip() if "," in location else location
                            generate_spot_description(spot, location, country, weather_data)
                        
                        # Reset question history when selecting a new spot
                        if st.session_state.selected_spot["id"] != spot["id"]:
                            st.session_state.question_history = []
                        
                        # Reset active tab
                        st.session_state.active_tab = "info"
                        
                        # Rerun to update UI
                        st.rerun()
                    
                    st.markdown(f"</div>", unsafe_allow_html=True)
    
    # Display selected spot details
    if st.session_state.selected_spot:
        spot = st.session_state.selected_spot
        
        st.markdown(f"<div class='sub-header'>🏠 {spot['name']}</div>", unsafe_allow_html=True)
        st.markdown(f"**Category:** {spot['category']}")
        
        # Create tabs for different sections
        tab_info, tab_map, tab_qa, tab_social = st.tabs(["📝 Information", "🗺️ Map", "❓ Q&A", "👥 Social"])
        
        # Set active tab based on session state
        if st.session_state.active_tab == "info":
            tab_info.active = True
        elif st.session_state.active_tab == "map":
            tab_map.active = True
        elif st.session_state.active_tab == "qa":
            tab_qa.active = True
        elif st.session_state.active_tab == "social":
            tab_social.active = True
        
        with tab_info:
            st.session_state.active_tab = "info"
            
            # Weather information
            if st.session_state.weather_data:
                st.markdown("<div class='weather-box'>", unsafe_allow_html=True)
                st.markdown("### Current Weather")
                create_weather_widget(st.session_state.weather_data)
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Spot description
            if st.session_state.spot_description:
                st.markdown("<div class='highlight-box'>", unsafe_allow_html=True)
                st.markdown("### About This Place")
                st.markdown(st.session_state.spot_description)
                st.markdown("</div>", unsafe_allow_html=True)
            
            # External links
            st.markdown("### External Links")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.session_state.user_location:
                    directions_url = get_google_maps_direction_url(
                        st.session_state.user_location["lat"],
                        st.session_state.user_location["lon"],
                        spot["lat"],
                        spot["lon"]
                    )
                    st.markdown(f"[🚗 Get Directions]({directions_url})")
            
            with col2:
                search_url = get_google_search_url(f"{spot['name']} {st.session_state.last_search.get('location', '')}")
                st.markdown(f"[🔍 Search on Google]({search_url})")
        
        with tab_map:
            st.session_state.active_tab = "map"
            
            # Get detailed map for the selected spot
            try:
                map_response = requests.post(f"{BACKEND_URL}/map/selected", json=spot)
                
                if map_response.status_code == 200:
                    st.components.v1.html(map_response.text, height=400)
                else:
                    st.error("Failed to load detailed map")
            except Exception as e:
                st.error(f"Error loading map: {str(e)}")
        
        with tab_qa:
            st.session_state.active_tab = "qa"
            
            st.markdown("### Ask About This Place")
            st.markdown("Ask any question about this tourist spot, local customs, best time to visit, etc.")
            
            # Use a form to properly handle the input clearing
            with st.form("question_form", clear_on_submit=True):
                question = st.text_input("Your Question", key="question_input")
                submitted = st.form_submit_button("Ask")
                
                if submitted and question:
                    location = st.session_state.last_search.get("location", "")
                    country = location.split(",")[-1].strip() if "," in location else location
                    answer = ask_question_about_spot(
                        spot, 
                        location, 
                        country, 
                        question, 
                        st.session_state.weather_data
                    )
                    if answer:
                        st.success("Question answered!")
                        # The form will automatically clear on submit due to clear_on_submit=True
                        # Rerun to update UI
                        st.rerun()
                elif submitted and not question:
                    st.warning("Please enter a question")
            
            # Display question history
            if st.session_state.question_history:
                st.markdown("### Previous Questions")
                for item in reversed(st.session_state.question_history):
                    with st.expander(f"Q: {item['question']} ({item['timestamp']})"):
                        st.markdown(f"**A:** {item['answer']}")
        
        with tab_social:
            st.session_state.active_tab = "social"
            
            # Social media interface for the selected spot
            st.markdown("### Share Your Experience")
            
            # Create post section
            social_interface.render_post_creation_ui(spot)
            
            # Display posts for this spot with enhanced viewing interface
            post_viewing_interface.render_posts(spot["id"])
            
            # Render media viewer if active
            post_viewing_interface.render_media_viewer()

    # Display user's own posts in sidebar if authenticated
    if st.session_state.is_authenticated and st.session_state.user_info:
        with st.sidebar.expander("My Posts", expanded=False):
            post_viewing_interface.render_user_posts()

if __name__ == "__main__":
    main()
