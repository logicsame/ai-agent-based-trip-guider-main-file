import unittest
import os
import sys
from dotenv import load_dotenv
import requests
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up test environment
load_dotenv()

class TestTouristSpotSearch(unittest.TestCase):
    """Test cases for Tourist Spot Search functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.base_url = "http://127.0.0.1:8000"
    
    def test_01_search_tourist_spots(self):
        """Test searching for tourist spots"""
        print("\nTesting tourist spot search...")
        
        # Search for tourist spots
        location = "New York"
        radius = 10
        
        response = requests.post(
            f"{self.base_url}/search",
            json={"location": location, "radius": radius}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200, f"Search failed: {response.text}")
        
        # Verify response data
        spots = response.json()
        self.assertIsInstance(spots, list)
        
        if len(spots) > 0:
            # Verify spot structure
            spot = spots[0]
            self.assertIn("id", spot)
            self.assertIn("name", spot)
            self.assertIn("category", spot)
            self.assertIn("lat", spot)
            self.assertIn("lon", spot)
            
            print(f"✅ Found {len(spots)} tourist spots near {location}")
        else:
            print(f"⚠️ No tourist spots found near {location}, but API call was successful")
    
    def test_02_get_weather_data(self):
        """Test getting weather data"""
        print("\nTesting weather data retrieval...")
        
        # Get weather data for a location
        lat = 40.7128  # New York
        lon = -74.0060
        
        response = requests.get(
            f"{self.base_url}/weather?lat={lat}&lon={lon}"
        )
        
        # Check response
        self.assertEqual(response.status_code, 200, f"Weather data retrieval failed: {response.text}")
        
        # Verify response data
        weather_data = response.json()
        self.assertIn("temperature", weather_data)
        self.assertIn("description", weather_data)
        
        print("✅ Weather data retrieval successful")
    
    def test_03_generate_description(self):
        """Test generating spot description"""
        print("\nTesting spot description generation...")
        
        # Create a test spot
        spot = {
            "spot_id": "test_spot_1",
            "spot_name": "Central Park",
            "spot_category": "Park",
            "location": "New York",
            "country": "USA"
        }
        
        response = requests.post(
            f"{self.base_url}/generate_description",
            json=spot
        )
        
        # Check response
        self.assertEqual(response.status_code, 200, f"Description generation failed: {response.text}")
        
        # Verify response data
        description = response.text
        self.assertIsInstance(description, str)
        self.assertGreater(len(description), 0)
        
        print("✅ Spot description generation successful")
    
    def test_04_ask_question(self):
        """Test asking a question about a spot"""
        print("\nTesting question answering...")
        
        # Create a test question
        question_data = {
            "spot_id": "test_spot_1",
            "spot_name": "Central Park",
            "spot_category": "Park",
            "location": "New York",
            "country": "USA",
            "question": "What are the best activities to do here?"
        }
        
        response = requests.post(
            f"{self.base_url}/ask_question",
            json=question_data
        )
        
        # Check response
        self.assertEqual(response.status_code, 200, f"Question answering failed: {response.text}")
        
        # Verify response data
        answer = response.text
        self.assertIsInstance(answer, str)
        self.assertGreater(len(answer), 0)
        
        print("✅ Question answering successful")
    
    def test_05_generate_map(self):
        """Test generating a map for spots"""
        print("\nTesting map generation...")
        
        # Create test spots
        spots = [
            {
                "id": "test_spot_1",
                "name": "Central Park",
                "category": "Park",
                "lat": 40.7812,
                "lon": -73.9665,
                "tags": {}
            },
            {
                "id": "test_spot_2",
                "name": "Empire State Building",
                "category": "Landmark",
                "lat": 40.7484,
                "lon": -73.9857,
                "tags": {}
            }
        ]
        
        # Create map request
        map_request = {
            "spots": spots,
            "center_lat": 40.7128,
            "center_lon": -74.0060,
            "radius": 10
        }
        
        response = requests.post(
            f"{self.base_url}/map/all",
            json=map_request
        )
        
        # Check response
        self.assertEqual(response.status_code, 200, f"Map generation failed: {response.text}")
        
        # Verify response data
        map_html = response.text
        self.assertIsInstance(map_html, str)
        self.assertGreater(len(map_html), 0)
        self.assertIn("<html", map_html.lower())
        self.assertIn("leaflet", map_html.lower())
        
        print("✅ Map generation successful")

if __name__ == "__main__":
    unittest.main()
