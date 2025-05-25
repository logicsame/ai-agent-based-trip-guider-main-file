import unittest
import os
import sys
from dotenv import load_dotenv
import requests
import time

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up test environment
load_dotenv()

class TestIntegration(unittest.TestCase):
    """Integration tests for Tourist Spot Social Media application"""
    
    def setUp(self):
        """Set up test environment"""
        self.base_url = "http://127.0.0.1:8000"
        self.test_username = f"testuser_{int(time.time())}"
        self.test_password = "Test@123456"
        self.test_email = f"test_{int(time.time())}@example.com"
        self.test_location = "New York"
        self.access_token = None
    
    def test_01_end_to_end_flow(self):
        """Test the complete end-to-end flow"""
        print("\nTesting end-to-end flow...")
        
        # Step 1: Register a new user
        print("Step 1: Registering a new user...")
        register_data = {
            "username": self.test_username,
            "email": self.test_email,
            "password": self.test_password,
            "full_name": "Test User"
        }
        
        response = requests.post(
            f"{self.base_url}/auth/register",
            json=register_data
        )
        
        self.assertEqual(response.status_code, 200, f"Registration failed: {response.text}")
        
        # Step 2: Login with the new user
        print("Step 2: Logging in...")
        login_data = {
            "username": self.test_username,
            "password": self.test_password
        }
        
        response = requests.post(
            f"{self.base_url}/auth/token",
            data=login_data
        )
        
        self.assertEqual(response.status_code, 200, f"Login failed: {response.text}")
        token_data = response.json()
        self.access_token = token_data["access_token"]
        
        # Step 3: Search for tourist spots
        print("Step 3: Searching for tourist spots...")
        search_data = {
            "location": self.test_location,
            "radius": 10
        }
        
        response = requests.post(
            f"{self.base_url}/search",
            json=search_data
        )
        
        self.assertEqual(response.status_code, 200, f"Search failed: {response.text}")
        spots = response.json()
        
        # If no spots found, create a test spot
        if not spots:
            print("No spots found, using a test spot...")
            test_spot = {
                "id": "test_spot_1",
                "name": "Central Park",
                "category": "Park",
                "lat": 40.7812,
                "lon": -73.9665,
                "tags": {}
            }
        else:
            test_spot = spots[0]
        
        # Step 4: Create a post for the spot
        print("Step 4: Creating a post...")
        post_data = {
            "spot_id": test_spot["id"],
            "spot_name": test_spot["name"],
            "title": f"Test Post about {test_spot['name']}",
            "content": f"This is a test post about {test_spot['name']}. It's a beautiful place to visit!",
            "media_ids": [],
            "lat": test_spot["lat"],
            "lon": test_spot["lon"],
            "tags": ["test", "travel", "tourism"]
        }
        
        response = requests.post(
            f"{self.base_url}/social/posts",
            headers={"Authorization": f"Bearer {self.access_token}"},
            data=post_data
        )
        
        self.assertEqual(response.status_code, 200, f"Create post failed: {response.text}")
        post = response.json()
        post_id = post["id"]
        
        # Step 5: Get posts for the spot
        print("Step 5: Getting posts for the spot...")
        response = requests.get(
            f"{self.base_url}/social/posts/spot/{test_spot['id']}",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        
        self.assertEqual(response.status_code, 200, f"Get posts failed: {response.text}")
        posts = response.json()
        self.assertGreater(len(posts), 0, "No posts found for the spot")
        
        # Step 6: Add a comment to the post
        print("Step 6: Adding a comment...")
        comment_data = {
            "content": "This is a test comment on the post."
        }
        
        response = requests.post(
            f"{self.base_url}/social/posts/{post_id}/comments",
            headers={"Authorization": f"Bearer {self.access_token}"},
            data=comment_data
        )
        
        self.assertEqual(response.status_code, 200, f"Create comment failed: {response.text}")
        comment = response.json()
        
        # Step 7: Get comments for the post
        print("Step 7: Getting comments for the post...")
        response = requests.get(
            f"{self.base_url}/social/posts/{post_id}/comments",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        
        self.assertEqual(response.status_code, 200, f"Get comments failed: {response.text}")
        comments = response.json()
        self.assertGreater(len(comments), 0, "No comments found for the post")
        
        # Step 8: Like the post
        print("Step 8: Liking the post...")
        response = requests.post(
            f"{self.base_url}/social/posts/{post_id}/like",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        
        self.assertEqual(response.status_code, 200, f"Like post failed: {response.text}")
        
        # Step 9: Get user profile
        print("Step 9: Getting user profile...")
        response = requests.get(
            f"{self.base_url}/auth/me",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        
        self.assertEqual(response.status_code, 200, f"Get profile failed: {response.text}")
        user_data = response.json()
        self.assertEqual(user_data["username"], self.test_username)
        
        print("✅ End-to-end flow test successful!")

if __name__ == "__main__":
    unittest.main()
