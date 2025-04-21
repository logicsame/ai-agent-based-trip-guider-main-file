from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from bson import ObjectId
from .auth_service import auth_service, ACCESS_TOKEN_EXPIRE_MINUTES
from .models import UserCreate, UserResponse, Token, UserUpdate, UserProfile
import logging

# Set up logging
logger = logging.getLogger("AuthRoutes")

# Create router
router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={404: {"description": "Not found"}},
)

@router.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate):
    """Register a new user"""
    try:
        created_user = auth_service.create_user(user)
        return created_user
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while registering user"
        )

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and get access token"""
    user = auth_service.authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": user["username"], "id": str(user["_id"])},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserProfile)
async def read_users_me(current_user: dict = Depends(auth_service.get_current_user)):
    """Get current user profile"""
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: dict = Depends(auth_service.get_current_user)
):
    """Update user profile"""
    try:
        # Get database
        db = auth_service.db
        
        # Prepare update data
        update_data = {}
        if user_update.full_name is not None:
            update_data["full_name"] = user_update.full_name
        if user_update.bio is not None:
            update_data["bio"] = user_update.bio
        if user_update.profile_picture is not None:
            update_data["profile_picture"] = user_update.profile_picture
        
        # Update user in database
        if update_data:
            result = db.users.update_one(
                {"_id": ObjectId(current_user["id"])},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User profile not updated"
                )
        
        # Get updated user
        updated_user = auth_service.get_user_by_id(current_user["id"])
        
        # Convert ObjectId to string for response
        updated_user["id"] = str(updated_user["_id"])
        del updated_user["_id"]
        del updated_user["password_hash"]
        
        return updated_user
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating user profile"
        )
