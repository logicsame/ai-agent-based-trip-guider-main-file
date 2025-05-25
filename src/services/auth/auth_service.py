import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Optional
from bson import ObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from .database import get_database
from .models import UserCreate, UserResponse, TokenData
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger("AuthService")

# Constants
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-jwt-please-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class AuthService:
    def __init__(self):
        self.db = get_database()
    
    def get_user_by_username(self, username: str):
        """Get user by username"""
        return self.db.users.find_one({"username": username})
    
    def get_user_by_email(self, email: str):
        """Get user by email"""
        return self.db.users.find_one({"email": email})
    
    def get_user_by_id(self, user_id: str):
        """Get user by ID"""
        return self.db.users.find_one({"_id": ObjectId(user_id)})
    
    def create_user(self, user: UserCreate):
        """Create a new user"""
        # Check if username already exists
        if self.get_user_by_username(user.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email already exists
        if self.get_user_by_email(user.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        hashed_password = self._get_password_hash(user.password)
        
        # Create user document
        user_data = {
            "username": user.username,
            "email": user.email,
            "password_hash": hashed_password,
            "full_name": user.full_name,
            "profile_picture": None,
            "bio": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "visited_spots": []
        }
        
        # Insert user into database
        result = self.db.users.insert_one(user_data)
        
        # Get created user
        created_user = self.get_user_by_id(result.inserted_id)
        
        # Convert ObjectId to string for response
        created_user["id"] = str(created_user["_id"])
        del created_user["_id"]
        del created_user["password_hash"]
        
        return created_user
    
    def authenticate_user(self, username: str, password: str):
        """Authenticate user with username and password"""
        user = self.get_user_by_username(username)
        
        if not user:
            return False
        
        if not self._verify_password(password, user["password_hash"]):
            return False
        
        return user
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        return encoded_jwt
    
    async def get_current_user(self, token: str = Depends(oauth2_scheme)):
        """Get current user from JWT token"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            user_id: str = payload.get("id")
            
            if username is None or user_id is None:
                raise credentials_exception
            
            token_data = TokenData(username=username, user_id=user_id)
        except JWTError:
            raise credentials_exception
        
        user = self.get_user_by_id(token_data.user_id)
        
        if user is None:
            raise credentials_exception
        
        # Convert ObjectId to string for response
        user["id"] = str(user["_id"])
        del user["_id"]
        del user["password_hash"]
        
        return user
    
    def _get_password_hash(self, password: str):
        """Hash password using bcrypt"""
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password_bytes, salt)
        return hashed_password.decode('utf-8')
    
    def _verify_password(self, plain_password: str, hashed_password: str):
        """Verify password against hash"""
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)

# Create a singleton instance
auth_service = AuthService()

def get_auth_service():
    """Get auth service instance"""
    return auth_service
