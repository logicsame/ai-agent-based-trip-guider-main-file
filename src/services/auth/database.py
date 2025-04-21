from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger("MongoDB")

class MongoDB:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDB, cls).__new__(cls)
            cls._instance.client = None
            cls._instance.db = None
            cls._instance.initialize_connection()
        return cls._instance
    
    def initialize_connection(self):
        """Initialize MongoDB connection"""
        try:
            # Get MongoDB connection string from environment variables or use default
            mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
            db_name = os.getenv("MONGODB_DB", "tourist_social_db")
            
            # Connect to MongoDB
            self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            
            # Check if connection is successful
            self.client.admin.command('ping')
            
            # Get database
            self.db = self.client[db_name]
            
            logger.info(f"Connected to MongoDB: {db_name}")
            
            # Create indexes for collections
            self._create_indexes()
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            self.client = None
            self.db = None
    
    def _create_indexes(self):
        """Create indexes for collections"""
        if self.db is None:
            return
        
        try:
            # User collection indexes
            self.db.users.create_index("username", unique=True)
            self.db.users.create_index("email", unique=True)
            
            # Post collection indexes
            self.db.posts.create_index("user_id")
            self.db.posts.create_index("spot_id")
            self.db.posts.create_index("created_at")
            self.db.posts.create_index([("location", "2dsphere")])
            
            # Comment collection indexes
            self.db.comments.create_index("post_id")
            self.db.comments.create_index("user_id")
            self.db.comments.create_index("created_at")
            
            logger.info("MongoDB indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating MongoDB indexes: {str(e)}")
    
    def get_db(self):
        """Get database instance"""
        if self.db is None:
            self.initialize_connection()
        return self.db
    
    def close_connection(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

# Create a singleton instance
mongodb = MongoDB()

def get_database():
    """Get database instance"""
    return mongodb.get_db()
