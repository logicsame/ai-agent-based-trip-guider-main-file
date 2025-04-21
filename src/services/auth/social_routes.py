from fastapi import APIRouter, Depends, HTTPException, status, Form
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from .auth_service import auth_service
import logging

# Set up logging
logger = logging.getLogger("SocialRoutes")

# Create router
router = APIRouter(
    prefix="/social",
    tags=["social"],
    responses={404: {"description": "Not found"}},
)

@router.post("/posts")
async def create_post(
    spot_id: str = Form(...),
    spot_name: str = Form(...),
    title: str = Form(...),
    content: str = Form(...),
    media_ids: List[str] = Form([]),
    lat: float = Form(...),
    lon: float = Form(...),
    tags: List[str] = Form([]),
    current_user: dict = Depends(auth_service.get_current_user)
):
    """Create a new post for a tourist spot"""
    try:
        # Get media documents
        media_list = []
        if media_ids:
            for media_id in media_ids:
                media = auth_service.db.media.find_one({
                    "_id": ObjectId(media_id),
                    "user_id": ObjectId(current_user["id"])
                })
                
                if media:
                    media_list.append({
                        "type": media["type"],
                        "url": media["url"],
                        "thumbnail_url": media["thumbnail_url"],
                        "caption": media["caption"]
                    })
        
        # Create post document
        post_data = {
            "user_id": ObjectId(current_user["id"]),
            "spot_id": spot_id,
            "spot_name": spot_name,
            "location": {
                "type": "Point",
                "coordinates": [lon, lat]  # GeoJSON format: [longitude, latitude]
            },
            "title": title,
            "content": content,
            "media": media_list,
            "tags": tags,
            "likes": [],
            "like_count": 0,
            "comment_count": 0,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # Insert post into database
        result = auth_service.db.posts.insert_one(post_data)
        
        # Update user's visited spots if not already visited
        spot_exists = auth_service.db.users.find_one({
            "_id": ObjectId(current_user["id"]),
            "visited_spots.spot_id": spot_id
        })
        
        if not spot_exists:
            auth_service.db.users.update_one(
                {"_id": ObjectId(current_user["id"])},
                {
                    "$push": {
                        "visited_spots": {
                            "spot_id": spot_id,
                            "spot_name": spot_name,
                            "visit_date": datetime.now()
                        }
                    }
                }
            )
        
        # Return post information
        return {
            "id": str(result.inserted_id),
            "user_id": current_user["id"],
            "spot_id": spot_id,
            "spot_name": spot_name,
            "title": title,
            "content": content,
            "media": media_list,
            "tags": tags,
            "like_count": 0,
            "comment_count": 0,
            "created_at": post_data["created_at"]
        }
    except Exception as e:
        logger.error(f"Error creating post: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating post"
        )

@router.get("/posts/spot/{spot_id}")
async def get_posts_by_spot(
    spot_id: str,
    current_user: dict = Depends(auth_service.get_current_user)
):
    """Get posts for a specific tourist spot"""
    try:
        # Query posts collection
        posts_cursor = auth_service.db.posts.find({"spot_id": spot_id}).sort("created_at", -1)
        
        # Convert cursor to list and format response
        posts_list = []
        for post in posts_cursor:
            # Get user information
            user = auth_service.db.users.find_one({"_id": post["user_id"]})
            user_info = {
                "id": str(user["_id"]),
                "username": user["username"],
                "full_name": user["full_name"],
                "profile_picture": user["profile_picture"]
            }
            
            posts_list.append({
                "id": str(post["_id"]),
                "user": user_info,
                "spot_id": post["spot_id"],
                "spot_name": post["spot_name"],
                "title": post["title"],
                "content": post["content"],
                "media": post["media"],
                "tags": post["tags"],
                "like_count": post["like_count"],
                "comment_count": post["comment_count"],
                "created_at": post["created_at"],
                "is_liked": str(current_user["id"]) in [str(uid) for uid in post.get("likes", [])]
            })
        
        return posts_list
    except Exception as e:
        logger.error(f"Error getting posts by spot: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while getting posts"
        )

@router.post("/posts/{post_id}/comments")
async def create_comment(
    post_id: str,
    content: str = Form(...),
    current_user: dict = Depends(auth_service.get_current_user)
):
    """Create a new comment on a post"""
    try:
        # Check if post exists
        post = auth_service.db.posts.find_one({"_id": ObjectId(post_id)})
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )
        
        # Create comment document
        comment_data = {
            "post_id": ObjectId(post_id),
            "user_id": ObjectId(current_user["id"]),
            "content": content,
            "likes": [],
            "like_count": 0,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # Insert comment into database
        result = auth_service.db.comments.insert_one(comment_data)
        
        # Increment comment count in post
        auth_service.db.posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$inc": {"comment_count": 1}}
        )
        
        # Return comment information
        return {
            "id": str(result.inserted_id),
            "post_id": post_id,
            "user": {
                "id": current_user["id"],
                "username": current_user["username"],
                "full_name": current_user["full_name"],
                "profile_picture": current_user["profile_picture"]
            },
            "content": content,
            "like_count": 0,
            "created_at": comment_data["created_at"]
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error creating comment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating comment"
        )

@router.get("/posts/{post_id}/comments")
async def get_post_comments(
    post_id: str,
    current_user: dict = Depends(auth_service.get_current_user)
):
    """Get comments for a specific post"""
    try:
        # Query comments collection
        comments_cursor = auth_service.db.comments.find({"post_id": ObjectId(post_id)}).sort("created_at", 1)
        
        # Convert cursor to list and format response
        comments_list = []
        for comment in comments_cursor:
            # Get user information
            user = auth_service.db.users.find_one({"_id": comment["user_id"]})
            user_info = {
                "id": str(user["_id"]),
                "username": user["username"],
                "full_name": user["full_name"],
                "profile_picture": user["profile_picture"]
            }
            
            comments_list.append({
                "id": str(comment["_id"]),
                "post_id": post_id,
                "user": user_info,
                "content": comment["content"],
                "like_count": comment["like_count"],
                "created_at": comment["created_at"],
                "is_liked": str(current_user["id"]) in [str(uid) for uid in comment.get("likes", [])]
            })
        
        return comments_list
    except Exception as e:
        logger.error(f"Error getting post comments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while getting comments"
        )

@router.post("/posts/{post_id}/like")
async def like_post(
    post_id: str,
    current_user: dict = Depends(auth_service.get_current_user)
):
    """Like or unlike a post"""
    try:
        # Check if post exists
        post = auth_service.db.posts.find_one({"_id": ObjectId(post_id)})
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )
        
        # Check if user already liked the post
        user_id_obj = ObjectId(current_user["id"])
        if user_id_obj in post.get("likes", []):
            # Unlike the post
            auth_service.db.posts.update_one(
                {"_id": ObjectId(post_id)},
                {
                    "$pull": {"likes": user_id_obj},
                    "$inc": {"like_count": -1}
                }
            )
            return {"message": "Post unliked successfully"}
        else:
            # Like the post
            auth_service.db.posts.update_one(
                {"_id": ObjectId(post_id)},
                {
                    "$addToSet": {"likes": user_id_obj},
                    "$inc": {"like_count": 1}
                }
            )
            return {"message": "Post liked successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error liking post: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while liking post"
        )

@router.get("/posts/user/{user_id}")
async def get_posts_by_user(
    user_id: str,
    current_user: dict = Depends(auth_service.get_current_user)
):
    """Get posts created by a specific user"""
    try:
        # Query posts collection
        posts_cursor = auth_service.db.posts.find({"user_id": ObjectId(user_id)}).sort("created_at", -1)
        
        # Convert cursor to list and format response
        posts_list = []
        for post in posts_cursor:
            # Get user information
            user = auth_service.db.users.find_one({"_id": post["user_id"]})
            user_info = {
                "id": str(user["_id"]),
                "username": user["username"],
                "full_name": user["full_name"],
                "profile_picture": user["profile_picture"]
            }
            
            posts_list.append({
                "id": str(post["_id"]),
                "user": user_info,
                "spot_id": post["spot_id"],
                "spot_name": post["spot_name"],
                "title": post["title"],
                "content": post["content"],
                "media": post["media"],
                "tags": post["tags"],
                "like_count": post["like_count"],
                "comment_count": post["comment_count"],
                "created_at": post["created_at"],
                "is_liked": str(current_user["id"]) in [str(uid) for uid in post.get("likes", [])]
            })
        
        return posts_list
    except Exception as e:
        logger.error(f"Error getting posts by user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while getting user posts"
        )

@router.get("/posts/trending")
async def get_trending_posts(
    limit: int = 3,
    current_user: dict = Depends(auth_service.get_current_user)
):
    """Get trending posts based on likes and comments"""
    try:
        # Query posts collection and sort by like_count and comment_count
        posts_cursor = auth_service.db.posts.find().sort([
            ("like_count", -1),
            ("comment_count", -1),
            ("created_at", -1)
        ]).limit(limit)
        
        # Convert cursor to list and format response
        posts_list = []
        for post in posts_cursor:
            # Get user information
            user = auth_service.db.users.find_one({"_id": post["user_id"]})
            user_info = {
                "id": str(user["_id"]),
                "username": user["username"],
                "full_name": user["full_name"],
                "profile_picture": user["profile_picture"]
            }
            
            posts_list.append({
                "id": str(post["_id"]),
                "user": user_info,
                "spot_id": post["spot_id"],
                "spot_name": post["spot_name"],
                "title": post["title"],
                "content": post["content"],
                "media": post["media"],
                "tags": post["tags"],
                "like_count": post["like_count"],
                "comment_count": post["comment_count"],
                "created_at": post["created_at"],
                "is_liked": str(current_user["id"]) in [str(uid) for uid in post.get("likes", [])]
            })
        
        return posts_list
    except Exception as e:
        logger.error(f"Error getting trending posts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while getting trending posts"
        )

@router.post("/comments/{comment_id}/like")
async def like_comment(
    comment_id: str,
    current_user: dict = Depends(auth_service.get_current_user)
):
    """Like or unlike a comment"""
    try:
        # Check if comment exists
        comment = auth_service.db.comments.find_one({"_id": ObjectId(comment_id)})
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )
        
        # Check if user already liked the comment
        user_id_obj = ObjectId(current_user["id"])
        if user_id_obj in comment.get("likes", []):
            # Unlike the comment
            auth_service.db.comments.update_one(
                {"_id": ObjectId(comment_id)},
                {
                    "$pull": {"likes": user_id_obj},
                    "$inc": {"like_count": -1}
                }
            )
            return {"message": "Comment unliked successfully"}
        else:
            # Like the comment
            auth_service.db.comments.update_one(
                {"_id": ObjectId(comment_id)},
                {
                    "$addToSet": {"likes": user_id_obj},
                    "$inc": {"like_count": 1}
                }
            )
            return {"message": "Comment liked successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error liking comment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while liking comment"
        )
