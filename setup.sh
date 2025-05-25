#!/bin/bash

# This script helps set up and run the Tourist Spot Social Media application

# Colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Tourist Spot Social Media - Setup Script${NC}"
echo "========================================"
echo

# Check if Python is installed
if command -v python3 &>/dev/null; then
    echo -e "${GREEN}✓ Python is installed${NC}"
    python3 --version
else
    echo -e "${RED}✗ Python 3 is not installed. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

# Check if pip is installed
if command -v pip3 &>/dev/null; then
    echo -e "${GREEN}✓ pip is installed${NC}"
    pip3 --version
else
    echo -e "${RED}✗ pip is not installed. Please install pip.${NC}"
    exit 1
fi

# Create virtual environment
echo
echo -e "${YELLOW}Creating virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Install requirements
echo
echo -e "${YELLOW}Installing requirements...${NC}"
pip3 install -r requirements.txt

# Create uploads directory
echo
echo -e "${YELLOW}Creating uploads directory...${NC}"
mkdir -p uploads/images uploads/videos
chmod 755 uploads

# Check if .env file exists
if [ ! -f .env ]; then
    echo
    echo -e "${YELLOW}Creating .env file...${NC}"
    cat > .env << EOF
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB=tourist_social_db

# JWT Authentication
SECRET_KEY=your-secret-key-for-jwt-please-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application Settings
UPLOAD_DIR=uploads
EOF
    echo -e "${GREEN}✓ Created .env file${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Setup MongoDB
echo
echo -e "${YELLOW}Would you like to setup MongoDB? (y/n)${NC}"
read -r setup_mongodb

if [ "$setup_mongodb" = "y" ]; then
    echo
    echo -e "${YELLOW}Choose MongoDB setup option:${NC}"
    echo "1. Install MongoDB locally (requires sudo privileges)"
    echo "2. Use MongoDB Atlas (cloud-hosted MongoDB)"
    read -r mongodb_option

    if [ "$mongodb_option" = "1" ]; then
        echo
        echo -e "${YELLOW}Setting up local MongoDB...${NC}"
        python3 setup_mongodb.py --install
    elif [ "$mongodb_option" = "2" ]; then
        echo
        echo -e "${YELLOW}Setting up MongoDB Atlas...${NC}"
        python3 setup_mongodb.py --atlas
    else
        echo -e "${RED}Invalid option. Skipping MongoDB setup.${NC}"
    fi
fi

# Ask if user wants to create mock data
echo
echo -e "${YELLOW}Would you like to create mock data for testing? (y/n)${NC}"
read -r create_mock_data

if [ "$create_mock_data" = "y" ]; then
    echo
    echo -e "${YELLOW}Creating mock data...${NC}"
    python3 setup_mongodb.py --mock-data
fi

# Start the application
echo
echo -e "${YELLOW}Choose what to start:${NC}"
echo "1. Backend API only"
echo "2. Frontend only"
echo "3. Both backend and frontend"
read -r start_option

if [ "$start_option" = "1" ]; then
    echo
    echo -e "${YELLOW}Starting backend API...${NC}"
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
elif [ "$start_option" = "2" ]; then
    echo
    echo -e "${YELLOW}Starting frontend...${NC}"
    streamlit run test_enhanced.py
elif [ "$start_option" = "3" ]; then
    echo
    echo -e "${YELLOW}Starting backend API and frontend...${NC}"
    echo -e "${YELLOW}Please open a new terminal and run: streamlit run test_enhanced.py${NC}"
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
else
    echo -e "${RED}Invalid option. Exiting.${NC}"
    exit 1
fi
