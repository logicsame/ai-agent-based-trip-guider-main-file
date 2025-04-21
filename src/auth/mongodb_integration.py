import os
import sys
from dotenv import load_dotenv
from services.auth.mongodb_setup import setup_mongodb_connection, create_mock_data
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MongoDBIntegration")

def main():
    """
    Main function to setup MongoDB and create mock data
    """
    # Load environment variables
    load_dotenv()
    
    # Setup MongoDB connection
    logger.info("Setting up MongoDB connection...")
    client, db = setup_mongodb_connection()
    
    if client and db:
        logger.info("MongoDB connection successful!")
        
        # Create mock data for testing
        logger.info("Creating mock data for testing...")
        create_mock_data(db)
        
        logger.info("MongoDB integration complete!")
        
        # Close connection
        client.close()
        return True
    else:
        logger.error("Failed to connect to MongoDB. Please check your configuration.")
        return False

if __name__ == "__main__":
    main()
