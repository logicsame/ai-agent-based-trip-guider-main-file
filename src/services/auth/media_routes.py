from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from .auth_service import auth_service
import os
import shutil
import uuid
import logging

# Set up logging
logger = logging.getLogger("MediaRoutes")

# Create router
router = APIRouter(
    prefix="/media",
    tags=["media"],
    responses={404: {"description": "Not found"}},
)

# Define upload directory
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_media(
    file: UploadFile = File(...),
    caption: str = Form(None),
    current_user: dict = Depends(auth_service.get_current_user)
):
    """Upload media file (image or video)"""
    try:
        # Check file type
        content_type = file.content_type
        if content_type is None:
            # Try to determine file type from extension
            file_extension = os.path.splitext(file.filename)[1].lower()
            if file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']:
                content_type = "image/jpeg"
            elif file_extension in ['.mp4', '.mov', '.avi', '.wmv', '.mkv']:
                content_type = "video/mp4"
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unable to determine file type. Only image or video files are allowed"
                )
        
        if not (content_type.startswith("image/") or content_type.startswith("video/")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only image or video files are allowed"
            )
        
        # Determine file type
        file_type = "image" if content_type.startswith("image/") else "video"
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Create user directory if it doesn't exist
        user_dir = os.path.join(UPLOAD_DIR, str(current_user["id"]))
        os.makedirs(user_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(user_dir, unique_filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Generate URL for the file
        # In production, this would be a CDN URL or a proper file serving URL
        file_url = f"/uploads/{current_user['id']}/{unique_filename}"
        
        # Create media document
        media_data = {
            "user_id": ObjectId(current_user["id"]),
            "type": file_type,
            "url": file_url,
            "thumbnail_url": file_url if file_type == "image" else None,
            "caption": caption,
            "size": os.path.getsize(file_path),
            "created_at": datetime.now()
        }
        
        # Insert media into database
        result = auth_service.db.media.insert_one(media_data)
        
        # Return media information
        return {
            "id": str(result.inserted_id),
            "type": file_type,
            "url": file_url,
            "thumbnail_url": media_data["thumbnail_url"],
            "caption": caption,
            "created_at": media_data["created_at"]
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error uploading media: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while uploading media"
        )

@router.get("/user/{user_id}")
async def get_user_media(
    user_id: str,
    current_user: dict = Depends(auth_service.get_current_user)
):
    """Get media files uploaded by a user"""
    try:
        # Query media collection
        media_cursor = auth_service.db.media.find({"user_id": ObjectId(user_id)})
        
        # Convert cursor to list and format response
        media_list = []
        for media in media_cursor:
            media_list.append({
                "id": str(media["_id"]),
                "type": media["type"],
                "url": media["url"],
                "thumbnail_url": media["thumbnail_url"],
                "caption": media["caption"],
                "created_at": media["created_at"]
            })
        
        return media_list
    except Exception as e:
        logger.error(f"Error getting user media: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while getting user media"
        )

@router.delete("/{media_id}")
async def delete_media(
    media_id: str,
    current_user: dict = Depends(auth_service.get_current_user)
):
    """Delete media file"""
    try:
        # Get media document
        media = auth_service.db.media.find_one({
            "_id": ObjectId(media_id),
            "user_id": ObjectId(current_user["id"])
        })
        
        if not media:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media not found or you don't have permission to delete it"
            )
        
        # Delete file from filesystem
        file_path = os.path.join(UPLOAD_DIR, media["url"].lstrip("/uploads/"))
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete media document
        result = auth_service.db.media.delete_one({"_id": ObjectId(media_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete media"
            )
        
        return {"message": "Media deleted successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error deleting media: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting media"
        )
