import unittest
import os
import sys
import json
from dotenv import load_dotenv
import requests
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up test environment
load_dotenv()

class TestTouristSpotSocialMedia(unittest.TestCase):
    """Test cases for Tourist Spot Social Media application"""
    
    def setUp(self):
        """Set up test environment"""
        self.base_url = "http://127.0.0.1:8000"
        self.test_user = {
            "username": f"testuser_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "email": f"test_{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com",
            "password": "Test@123456",
            "full_name": "Test User"
        }
        self.access_token = None
    
    def test_01_user_registration(self):
        """Test user registration"""
        print("\nTesting user registration...")
        
        # Register a new user
        response = requests.post(
            f"{self.base_url}/auth/register",
            json=self.test_user
        )
        
        # Check response
        self.assertEqual(response.status_code, 200, f"Registration failed: {response.text}")
        
        # Verify response data
        user_data = response.json()
        self.assertEqual(user_data["username"], self.test_user["username"])
        self.assertEqual(user_data["email"], self.test_user["email"])
        self.assertEqual(user_data["full_name"], self.test_user["full_name"])
        
        print("✅ User registration successful")
    
    def test_02_user_login(self):
        """Test user login"""
        print("\nTesting user login...")
        
        # Login with the test user
        response = requests.post(
            f"{self.base_url}/auth/token",
            data={
                "username": self.test_user["username"],
                "password": self.test_user["password"]
            }
        )
        
        # Check response
        self.assertEqual(response.status_code, 200, f"Login failed: {response.text}")
        
        # Verify response data
        token_data = response.json()
        self.assertIn("access_token", token_data)
        self.assertIn("token_type", token_data)
        self.assertEqual(token_data["token_type"], "bearer")
        
        # Save token for later tests
        self.access_token = token_data["access_token"]
        
        print("✅ User login successful")
    
    def test_03_get_user_profile(self):
        """Test getting user profile"""
        print("\nTesting get user profile...")
        
        # Ensure we have a token
        if not self.access_token:
            self.test_02_user_login()
        
        # Get user profile
        response = requests.get(
            f"{self.base_url}/auth/me",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200, f"Get profile failed: {response.text}")
        
        # Verify response data
        user_data = response.json()
        self.assertEqual(user_data["username"], self.test_user["username"])
        self.assertEqual(user_data["email"], self.test_user["email"])
        self.assertEqual(user_data["full_name"], self.test_user["full_name"])
        
        print("✅ Get user profile successful")
    
    def test_04_update_user_profile(self):
        """Test updating user profile"""
        print("\nTesting update user profile...")
        
        # Ensure we have a token
        if not self.access_token:
            self.test_02_user_login()
        
        # Update profile data
        update_data = {
            "full_name": f"Updated Test User {datetime.now().strftime('%Y%m%d%H%M%S')}",
            "bio": "This is a test bio for the updated user profile."
        }
        
        # Update user profile
        response = requests.put(
            f"{self.base_url}/auth/me",
            headers={"Authorization": f"Bearer {self.access_token}"},
            json=update_data
        )
        
        # Check response
        self.assertEqual(response.status_code, 200, f"Update profile failed: {response.text}")
        
        # Verify response data
        user_data = response.json()
        self.assertEqual(user_data["full_name"], update_data["full_name"])
        self.assertEqual(user_data["bio"], update_data["bio"])
        
        print("✅ Update user profile successful")
    
    def test_05_create_post(self):
        """Test creating a post"""
        print("\nTesting post creation...")
        
        # Ensure we have a token
        if not self.access_token:
            self.test_02_user_login()
        
        # Create a test spot
        spot_id = "test_spot_1"
        spot_name = "Test Tourist Spot"
        
        # Create post data
        post_data = {
            "spot_id": spot_id,
            "spot_name": spot_name,
            "title": f"Test Post {datetime.now().strftime('%Y%m%d%H%M%S')}",
            "content": "This is a test post content for testing the post creation functionality.",
            "media_ids": [],
            "lat": 28.6139,
            "lon": 77.2090,
            "tags": ["test", "tourist", "spot"]
        }
        
        # Create post
        response = requests.post(
            f"{self.base_url}/social/posts",
            headers={"Authorization": f"Bearer {self.access_token}"},
            data=post_data
        )
        
        # Check response
        self.assertEqual(response.status_code, 200, f"Create post failed: {response.text}")
        
        # Verify response data
        post_data = response.json()
        self.assertEqual(post_data["spot_id"], spot_id)
        self.assertEqual(post_data["spot_name"], spot_name)
        self.assertEqual(post_data["title"], post_data["title"])
        self.assertEqual(post_data["content"], post_data["content"])
        
        # Save post ID for later tests
        self.post_id = post_data["id"]
        
        print("✅ Post creation successful")
    
    def test_06_get_posts_by_spot(self):
        """Test getting posts by spot"""
        print("\nTesting get posts by spot...")
        
        # Ensure we have a token
        if not self.access_token:
            self.test_02_user_login()
        
        # Ensure we have created a post
        if not hasattr(self, 'post_id'):
            self.test_05_create_post()
        
        # Get posts by spot
        response = requests.get(
            f"{self.base_url}/social/posts/spot/test_spot_1",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200, f"Get posts by spot failed: {response.text}")
        
        # Verify response data
        posts = response.json()
        self.assertIsInstance(posts, list)
        self.assertGreater(len(posts), 0)
        
        # Check if our post is in the list
        found = False
        for post in posts:
            if post["id"] == self.post_id:
                found = True
                break
        
        self.assertTrue(found, "Created post not found in spot posts")
        
        print("✅ Get posts by spot successful")
    
    def test_07_create_comment(self):
        """Test creating a comment"""
        print("\nTesting comment creation...")
        
        # Ensure we have a token
        if not self.access_token:
            self.test_02_user_login()
        
        # Ensure we have created a post
        if not hasattr(self, 'post_id'):
            self.test_05_create_post()
        
        # Create comment data
        comment_data = {
            "content": f"Test comment {datetime.now().strftime('%Y%m%d%H%M%S')}"
        }
        
        # Create comment
        response = requests.post(
            f"{self.base_url}/social/posts/{self.post_id}/comments",
            headers={"Authorization": f"Bearer {self.access_token}"},
            data=comment_data
        )
        
        # Check response
        self.assertEqual(response.status_code, 200, f"Create comment failed: {response.text}")
        
        # Verify response data
        comment_data = response.json()
        self.assertEqual(comment_data["post_id"], self.post_id)
        self.assertEqual(comment_data["content"], comment_data["content"])
        
        # Save comment ID for later tests
        self.comment_id = comment_data["id"]
        
        print("✅ Comment creation successful")
    
    def test_08_get_post_comments(self):
        """Test getting post comments"""
        print("\nTesting get post comments...")
        
        # Ensure we have a token
        if not self.access_token:
            self.test_02_user_login()
        
        # Ensure we have created a post and comment
        if not hasattr(self, 'post_id'):
            self.test_05_create_post()
        if not hasattr(self, 'comment_id'):
            self.test_07_create_comment()
        
        # Get post comments
        response = requests.get(
            f"{self.base_url}/social/posts/{self.post_id}/comments",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200, f"Get post comments failed: {response.text}")
        
        # Verify response data
        comments = response.json()
        self.assertIsInstance(comments, list)
        self.assertGreater(len(comments), 0)
        
        # Check if our comment is in the list
        found = False
        for comment in comments:
            if comment["id"] == self.comment_id:
                found = True
                break
        
        self.assertTrue(found, "Created comment not found in post comments")
        
        print("✅ Get post comments successful")
    
    def test_09_like_post(self):
        """Test liking a post"""
        print("\nTesting post like functionality...")
        
        # Ensure we have a token
        if not self.access_token:
            self.test_02_user_login()
        
        # Ensure we have created a post
        if not hasattr(self, 'post_id'):
            self.test_05_create_post()
        
        # Like post
        response = requests.post(
            f"{self.base_url}/social/posts/{self.post_id}/like",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200, f"Like post failed: {response.text}")
        
        # Verify response data
        like_data = response.json()
        self.assertIn("message", like_data)
        
        # Get posts by spot to check like count
        response = requests.get(
            f"{self.base_url}/social/posts/spot/test_spot_1",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        
        # Find our post
        posts = response.json()
        for post in posts:
            if post["id"] == self.post_id:
                self.assertTrue(post["is_liked"], "Post should be liked")
                self.assertGreater(post["like_count"], 0, "Like count should be greater than 0")
                break
        
        print("✅ Post like functionality successful")
    
    def test_10_like_comment(self):
        """Test liking a comment"""
        print("\nTesting comment like functionality...")
        
        # Ensure we have a token
        if not self.access_token:
            self.test_02_user_login()
        
        # Ensure we have created a comment
        if not hasattr(self, 'comment_id'):
            self.test_07_create_comment()
        
        # Like comment
        response = requests.post(
            f"{self.base_url}/social/comments/{self.comment_id}/like",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200, f"Like comment failed: {response.text}")
        
        # Verify response data
        like_data = response.json()
        self.assertIn("message", like_data)
        
        # Get post comments to check like count
        response = requests.get(
            f"{self.base_url}/social/posts/{self.post_id}/comments",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        
        # Find our comment
        comments = response.json()
        for comment in comments:
            if comment["id"] == self.comment_id:
                self.assertTrue(comment["is_liked"], "Comment should be liked")
                self.assertGreater(comment["like_count"], 0, "Like count should be greater than 0")
                break
        
        print("✅ Comment like functionality successful")

if __name__ == "__main__":
    unittest.main()
