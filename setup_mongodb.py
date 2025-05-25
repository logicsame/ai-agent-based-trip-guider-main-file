import os
import sys
import logging
from dotenv import load_dotenv
import argparse

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.auth.mongodb_setup import setup_mongodb_connection, create_mock_data
from services.auth.mongodb_installer import check_mongodb_installed, setup_mongodb_locally, setup_mongodb_atlas

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MongoDBSetupScript")

def main():
    """
    Main function to setup MongoDB for the Tourist Spot Social Media application
    """
    parser = argparse.ArgumentParser(description='Setup MongoDB for Tourist Spot Social Media')
    parser.add_argument('--install', action='store_true', help='Install MongoDB if not already installed')
    parser.add_argument('--atlas', action='store_true', help='Use MongoDB Atlas instead of local MongoDB')
    parser.add_argument('--mock-data', action='store_true', help='Create mock data for testing')
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Check if MongoDB is installed
    if not check_mongodb_installed():
        if args.install:
            logger.info("MongoDB not found. Installing...")
            if args.atlas:
                if not setup_mongodb_atlas():
                    logger.error("Failed to setup MongoDB Atlas. Exiting.")
                    return False
            else:
                if not setup_mongodb_locally():
                    logger.error("Failed to install MongoDB locally. Consider using MongoDB Atlas with --atlas flag.")
                    return False
        else:
            logger.error("MongoDB not found. Run with --install to install locally or --atlas to use MongoDB Atlas.")
            return False
    
    # Setup MongoDB connection
    logger.info("Setting up MongoDB connection...")
    client, db = setup_mongodb_connection()
    
    if client and db:
        logger.info("MongoDB connection successful!")
        
        # Create mock data for testing if requested
        if args.mock_data:
            logger.info("Creating mock data for testing...")
            create_mock_data(db)
        
        logger.info("MongoDB setup complete!")
        
        # Close connection
        client.close()
        return True
    else:
        logger.error("Failed to connect to MongoDB. Please check your configuration.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
