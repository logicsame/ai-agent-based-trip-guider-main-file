import pymongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MongoDBSetup")

# Load environment variables
load_dotenv()

def setup_mongodb_connection():
    """
    Setup MongoDB connection using MongoDB Atlas or local MongoDB
    
    This function will try to connect to MongoDB using the URI from environment variables.
    If local MongoDB is not available, it will provide instructions for using MongoDB Atlas.
    """
    try:
        # Get MongoDB URI from environment variables
        mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        db_name = os.getenv("MONGODB_DB", "tourist_social_db")
        
        # Create a new client and connect to the server
        client = MongoClient(mongodb_uri)
        
        # Send a ping to confirm a successful connection
        client.admin.command('ping')
        logger.info("Successfully connected to MongoDB!")
        
        # Get database
        db = client[db_name]
        
        # Create collections if they don't exist
        if "users" not in db.list_collection_names():
            db.create_collection("users")
            logger.info("Created 'users' collection")
        
        if "posts" not in db.list_collection_names():
            db.create_collection("posts")
            logger.info("Created 'posts' collection")
        
        if "comments" not in db.list_collection_names():
            db.create_collection("comments")
            logger.info("Created 'comments' collection")
        
        if "media" not in db.list_collection_names():
            db.create_collection("media")
            logger.info("Created 'media' collection")
        
        # Create indexes
        db.users.create_index("username", unique=True)
        db.users.create_index("email", unique=True)
        
        db.posts.create_index("user_id")
        db.posts.create_index("spot_id")
        db.posts.create_index("created_at")
        db.posts.create_index([("location", "2dsphere")])
        
        db.comments.create_index("post_id")
        db.comments.create_index("user_id")
        db.comments.create_index("created_at")
        
        logger.info("MongoDB indexes created successfully")
        
        return client, db
    
    except pymongo.errors.ConnectionFailure as e:
        logger.error(f"Could not connect to MongoDB: {e}")
        logger.info("Please make sure MongoDB is installed and running, or use MongoDB Atlas.")
        logger.info("MongoDB Atlas Setup Instructions:")
        logger.info("1. Create a free account at https://www.mongodb.com/cloud/atlas/register")
        logger.info("2. Create a new cluster")
        logger.info("3. Create a database user with read/write permissions")
        logger.info("4. Add your IP address to the IP Access List")
        logger.info("5. Get your connection string and update the MONGODB_URI in your .env file")
        return None, None
    
    except Exception as e:
        logger.error(f"An error occurred while setting up MongoDB: {e}")
        return None, None

def create_mock_data(db):
    """Create mock data for testing if the database is empty"""
    try:
        # Check if users collection is empty
        if db.users.count_documents({}) == 0:
            logger.info("Creating mock user data for testing...")
            
            # Create a test user
            from services.auth.auth_service import AuthService
            auth_service = AuthService()
            
            # Create test user
            from services.auth.models import UserCreate
            test_user = UserCreate(
                username="testuser",
                email="test@example.com",
                password="password123",
                full_name="Test User"
            )
            
            auth_service.create_user(test_user)
            logger.info("Created test user: testuser (password: password123)")
            
            # Get the created user
            user = db.users.find_one({"username": "testuser"})
            
            if user:
                # Create a test post
                from datetime import datetime
                from bson import ObjectId
                
                post_data = {
                    "user_id": user["_id"],
                    "spot_id": "test_spot_1",
                    "spot_name": "Test Tourist Spot",
                    "location": {
                        "type": "Point",
                        "coordinates": [77.2090, 28.6139]  # Example coordinates
                    },
                    "title": "My Amazing Trip",
                    "content": "This is a test post about my amazing trip to this tourist spot. The views were incredible and I had a great time!",
                    "media": [
                        {
                            "type": "image",
                            "url": "/static/test_image.jpg",
                            "thumbnail_url": "/static/test_image_thumb.jpg",
                            "caption": "Beautiful view"
                        }
                    ],
                    "tags": ["travel", "vacation", "sightseeing"],
                    "likes": [],
                    "like_count": 0,
                    "comment_count": 0,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
                
                result = db.posts.insert_one(post_data)
                logger.info(f"Created test post with ID: {result.inserted_id}")
                
                # Create a test comment
                comment_data = {
                    "post_id": result.inserted_id,
                    "user_id": user["_id"],
                    "content": "This is a test comment on my own post!",
                    "likes": [],
                    "like_count": 0,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
                
                comment_result = db.comments.insert_one(comment_data)
                logger.info(f"Created test comment with ID: {comment_result.inserted_id}")
                
                # Update post comment count
                db.posts.update_one(
                    {"_id": result.inserted_id},
                    {"$inc": {"comment_count": 1}}
                )
    
    except Exception as e:
        logger.error(f"Error creating mock data: {e}")

if __name__ == "__main__":
    # Setup MongoDB connection
    client, db = setup_mongodb_connection()
    
    if client and db:
        # Create mock data for testing
        create_mock_data(db)
        
        # Close connection
        client.close()
