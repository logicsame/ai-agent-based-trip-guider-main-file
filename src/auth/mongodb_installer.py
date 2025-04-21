import subprocess
import sys
import os
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MongoDBInstaller")

def check_mongodb_installed():
    """Check if MongoDB is installed"""
    try:
        # Try to run mongod --version
        result = subprocess.run(["mongod", "--version"], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE,
                               text=True)
        
        if result.returncode == 0:
            logger.info("MongoDB is already installed.")
            return True
        else:
            logger.info("MongoDB is not installed or not in PATH.")
            return False
    except FileNotFoundError:
        logger.info("MongoDB is not installed or not in PATH.")
        return False

def install_mongodb_ubuntu():
    """Install MongoDB on Ubuntu"""
    try:
        logger.info("Installing MongoDB...")
        
        # Import the MongoDB public GPG key
        logger.info("Importing MongoDB public GPG key...")
        subprocess.run([
            "wget", "-qO-", 
            "https://www.mongodb.org/static/pgp/server-6.0.asc", 
            "|", "sudo", "apt-key", "add", "-"
        ], check=True, shell=True)
        
        # Create a list file for MongoDB
        logger.info("Creating list file for MongoDB...")
        subprocess.run([
            "echo", "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse", 
            "|", "sudo", "tee", "/etc/apt/sources.list.d/mongodb-org-6.0.list"
        ], check=True, shell=True)
        
        # Update package database
        logger.info("Updating package database...")
        subprocess.run(["sudo", "apt-get", "update"], check=True)
        
        # Install MongoDB packages
        logger.info("Installing MongoDB packages...")
        subprocess.run([
            "sudo", "apt-get", "install", "-y", 
            "mongodb-org"
        ], check=True)
        
        # Start MongoDB service
        logger.info("Starting MongoDB service...")
        subprocess.run(["sudo", "systemctl", "start", "mongod"], check=True)
        
        # Enable MongoDB service to start on boot
        logger.info("Enabling MongoDB service to start on boot...")
        subprocess.run(["sudo", "systemctl", "enable", "mongod"], check=True)
        
        logger.info("MongoDB installed successfully!")
        return True
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing MongoDB: {e}")
        return False

def setup_mongodb_locally():
    """Setup MongoDB locally"""
    # Check if MongoDB is already installed
    if check_mongodb_installed():
        return True
    
    # Install MongoDB based on the operating system
    if sys.platform.startswith('linux'):
        # Check if it's Ubuntu
        if os.path.exists('/etc/lsb-release'):
            with open('/etc/lsb-release', 'r') as f:
                if 'Ubuntu' in f.read():
                    return install_mongodb_ubuntu()
        
        logger.error("Automatic installation is only supported on Ubuntu.")
        logger.info("Please install MongoDB manually following the instructions at:")
        logger.info("https://www.mongodb.com/docs/manual/administration/install-on-linux/")
        return False
    
    elif sys.platform == 'darwin':  # macOS
        logger.error("Automatic installation is not supported on macOS.")
        logger.info("Please install MongoDB manually using Homebrew:")
        logger.info("brew tap mongodb/brew")
        logger.info("brew install mongodb-community")
        logger.info("brew services start mongodb-community")
        return False
    
    elif sys.platform == 'win32':  # Windows
        logger.error("Automatic installation is not supported on Windows.")
        logger.info("Please install MongoDB manually following the instructions at:")
        logger.info("https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-windows/")
        return False
    
    else:
        logger.error(f"Unsupported operating system: {sys.platform}")
        return False

def setup_mongodb_atlas():
    """Provide instructions for setting up MongoDB Atlas"""
    logger.info("MongoDB Atlas Setup Instructions:")
    logger.info("1. Create a free account at https://www.mongodb.com/cloud/atlas/register")
    logger.info("2. Create a new cluster (the free tier is sufficient)")
    logger.info("3. Create a database user with read/write permissions")
    logger.info("4. Add your IP address to the IP Access List")
    logger.info("5. Get your connection string by clicking 'Connect' > 'Connect your application'")
    logger.info("6. Update the MONGODB_URI in your .env file with the connection string")
    logger.info("   Format: mongodb+srv://<username>:<password>@<cluster-url>/<dbname>?retryWrites=true&w=majority")
    
    # Ask user if they want to update the .env file
    response = input("Do you have a MongoDB Atlas connection string to update in .env? (y/n): ")
    
    if response.lower() == 'y':
        connection_string = input("Enter your MongoDB Atlas connection string: ")
        
        # Load environment variables
        load_dotenv()
        
        # Get the path to the .env file
        env_path = os.path.join(os.getcwd(), '.env')
        
        # Read the current .env file
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        # Update the MONGODB_URI line
        with open(env_path, 'w') as f:
            for line in lines:
                if line.startswith('MONGODB_URI='):
                    f.write(f'MONGODB_URI={connection_string}\n')
                else:
                    f.write(line)
        
        logger.info("Updated MONGODB_URI in .env file.")
        return True
    
    return False

def main():
    """Main function to setup MongoDB"""
    logger.info("MongoDB Setup Utility")
    logger.info("=====================")
    
    # Check if MongoDB is already installed
    if check_mongodb_installed():
        logger.info("MongoDB is already installed and ready to use.")
        return True
    
    # Ask user if they want to install MongoDB locally or use MongoDB Atlas
    logger.info("\nYou have two options for MongoDB:")
    logger.info("1. Install MongoDB locally (requires sudo privileges)")
    logger.info("2. Use MongoDB Atlas (cloud-hosted MongoDB)")
    
    choice = input("Enter your choice (1 or 2): ")
    
    if choice == '1':
        return setup_mongodb_locally()
    elif choice == '2':
        return setup_mongodb_atlas()
    else:
        logger.error("Invalid choice. Please run the script again and enter 1 or 2.")
        return False

if __name__ == "__main__":
    main()
