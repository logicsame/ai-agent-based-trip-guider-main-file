import streamlit as st
import requests
import json
from datetime import datetime
import os
import time
from PIL import Image
import io
import base64
from .url_utils import join_url_paths

class SocialMediaInterface:
    def __init__(self, backend_url="http://127.0.0.1:8000"):
        self.backend_url = backend_url
        
        # Initialize session state variables for auth
        if 'user_token' not in st.session_state:
            st.session_state.user_token = None
        if 'user_info' not in st.session_state:
            st.session_state.user_info = None
        if 'is_authenticated' not in st.session_state:
            st.session_state.is_authenticated = False
        if 'uploaded_media' not in st.session_state:
            st.session_state.uploaded_media = []
        if 'posts' not in st.session_state:
            st.session_state.posts = []
        if 'comments' not in st.session_state:
            st.session_state.comments = {}
        if 'show_comments' not in st.session_state:
            st.session_state.show_comments = {}
    
    def render_auth_ui(self):
        """Render authentication UI (login/register)"""
        st.sidebar.title("User Account")
        
        if st.session_state.is_authenticated:
            self._render_user_profile()
        else:
            self._render_login_register()
    
    def _render_login_register(self):
        """Render login and registration forms"""
        tab1, tab2 = st.sidebar.tabs(["Login", "Register"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit_button = st.form_submit_button("Login")
                
                if submit_button:
                    if self._login_user(username, password):
                        st.success("Login successful!")
                        st.rerun()
        
        with tab2:
            with st.form("register_form"):
                new_username = st.text_input("Username", key="reg_username")
                email = st.text_input("Email")
                full_name = st.text_input("Full Name")
                new_password = st.text_input("Password", type="password", key="reg_password")
                confirm_password = st.text_input("Confirm Password", type="password")
                submit_button = st.form_submit_button("Register")
                
                if submit_button:
                    if new_password != confirm_password:
                        st.error("Passwords do not match!")
                    elif len(new_password) < 8:
                        st.error("Password must be at least 8 characters long!")
                    else:
                        if self._register_user(new_username, email, full_name, new_password):
                            st.success("Registration successful! Please login.")
    
    def _render_user_profile(self):
        """Render user profile information"""
        if st.session_state.user_info:
            st.sidebar.write(f"Welcome, {st.session_state.user_info['full_name']}!")
            
            if st.session_state.user_info.get('profile_picture'):
                # Use the URL utility to properly join paths
                profile_pic_url = st.session_state.user_info['profile_picture']
                profile_pic_url = join_url_paths(self.backend_url, profile_pic_url)
                st.sidebar.image(profile_pic_url, width=100)
            
            if st.sidebar.button("Logout"):
                self._logout_user()
                st.rerun()
            
            with st.sidebar.expander("Edit Profile"):
                with st.form("edit_profile_form"):
                    full_name = st.text_input("Full Name", value=st.session_state.user_info.get('full_name', ''))
                    bio = st.text_area("Bio", value=st.session_state.user_info.get('bio', ''))
                    profile_pic = st.file_uploader("Profile Picture", type=["jpg", "jpeg", "png"])
                    update_button = st.form_submit_button("Update Profile")
                    
                    if update_button:
                        profile_pic_url = None
                        if profile_pic:
                            # Upload profile picture
                            files = {"file": profile_pic}
                            response = requests.post(
                                f"{self.backend_url}/media/upload",
                                headers={"Authorization": f"Bearer {st.session_state.user_token}"},
                                files=files,
                                data={"caption": "Profile picture"}
                            )
                            
                            if response.status_code == 200:
                                media_data = response.json()
                                profile_pic_url = media_data["url"]
                        
                        # Update profile
                        update_data = {
                            "full_name": full_name,
                            "bio": bio
                        }
                        
                        if profile_pic_url:
                            update_data["profile_picture"] = profile_pic_url
                        
                        response = requests.put(
                            f"{self.backend_url}/auth/me",
                            headers={"Authorization": f"Bearer {st.session_state.user_token}"},
                            json=update_data
                        )
                        
                        if response.status_code == 200:
                            st.session_state.user_info = response.json()
                            st.success("Profile updated successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to update profile!")
    
    def render_post_creation_ui(self, spot):
        """Render post creation UI for a selected tourist spot"""
        if not st.session_state.is_authenticated:
            st.warning("Please login to create posts!")
            return
        
        st.subheader("Share Your Experience")
        
        with st.form("create_post_form"):
            title = st.text_input("Title", placeholder="Give your post a title")
            content = st.text_area("Content", placeholder="Share your experience at this place...")
            
            # Media upload section
            uploaded_files = st.file_uploader(
                "Upload Images/Videos", 
                type=["jpg", "jpeg", "png", "mp4", "mov"], 
                accept_multiple_files=True
            )
            
            tags_input = st.text_input("Tags (comma separated)", placeholder="nature, adventure, food")
            
            submit_button = st.form_submit_button("Post")
            
            if submit_button:
                if not title or not content:
                    st.error("Title and content are required!")
                else:
                    # Process tags
                    tags = [tag.strip() for tag in tags_input.split(",")] if tags_input else []
                    
                    # Upload media files
                    media_ids = []
                    if uploaded_files:
                        with st.spinner("Uploading media..."):
                            for file in uploaded_files:
                                files = {"file": file}
                                response = requests.post(
                                    f"{self.backend_url}/media/upload",
                                    headers={"Authorization": f"Bearer {st.session_state.user_token}"},
                                    files=files,
                                    data={"caption": title}
                                )
                                
                                if response.status_code == 200:
                                    media_data = response.json()
                                    media_ids.append(media_data["id"])
                    
                    # Create post
                    with st.spinner("Creating post..."):
                        form_data = {
                            "spot_id": spot["id"],
                            "spot_name": spot["name"],
                            "title": title,
                            "content": content,
                            "media_ids": media_ids,
                            "lat": spot["lat"],
                            "lon": spot["lon"],
                            "tags": tags
                        }
                        
                        response = requests.post(
                            f"{self.backend_url}/social/posts",
                            headers={"Authorization": f"Bearer {st.session_state.user_token}"},
                            data=form_data
                        )
                        
                        if response.status_code == 200:
                            st.success("Post created successfully!")
                            # Refresh posts
                            self.load_posts_for_spot(spot["id"])
                        else:
                            st.error(f"Failed to create post: {response.text}")
    
    def render_posts_for_spot(self, spot_id):
        """Render posts for a specific tourist spot"""
        if not st.session_state.is_authenticated:
            st.warning("Please login to view posts!")
            return
        
        # Load posts if not already loaded
        if not st.session_state.posts:
            self.load_posts_for_spot(spot_id)
        
        if not st.session_state.posts:
            st.info("No posts yet for this spot. Be the first to share your experience!")
            return
        
        st.subheader("Traveler Experiences")
        
        # Render each post
        for post in st.session_state.posts:
            with st.container():
                st.markdown(f"### {post['title']}")
                
                # User info
                col1, col2 = st.columns([1, 5])
                with col1:
                    if post['user'].get('profile_picture'):
                        st.image(post['user']['profile_picture'], width=50)
                    else:
                        st.markdown("👤")
                
                with col2:
                    st.markdown(f"**{post['user']['full_name']}** (@{post['user']['username']})")
                    st.markdown(f"*{post['created_at'].split('T')[0]}*")
                
                # Post content
                st.markdown(post['content'])
                
                # Media gallery
                if post.get('media') and len(post['media']) > 0:
                    media_items = post['media']
                    cols = st.columns(min(3, len(media_items)))
                    
                    for i, media in enumerate(media_items):
                        col_idx = i % len(cols)
                        with cols[col_idx]:
                            if media['type'] == 'image':
                                # Use the URL utility to properly join paths
                                media_url = join_url_paths(self.backend_url, media['url'])
                                st.image(media_url, use_container_width=True)
                            elif media['type'] == 'video':
                                # Use the URL utility to properly join paths
                                media_url = join_url_paths(self.backend_url, media['url'])
                                st.video(media_url)
                
                # Tags
                if post.get('tags') and len(post['tags']) > 0:
                    st.markdown(" ".join([f"#{tag}" for tag in post['tags']]))
                
                # Like button
                col1, col2, col3 = st.columns([1, 1, 5])
                with col1:
                    like_label = "❤️" if post.get('is_liked') else "🤍"
                    like_count = post.get('like_count', 0)
                    if st.button(f"{like_label} {like_count}", key=f"like_{post['id']}"):
                        self._like_post(post['id'])
                
                # Comment button
                with col2:
                    comment_count = post.get('comment_count', 0)
                    if st.button(f"💬 {comment_count}", key=f"comment_{post['id']}"):
                        # Toggle comments visibility
                        st.session_state.show_comments[post['id']] = not st.session_state.show_comments.get(post['id'], False)
                        
                        # Load comments if showing
                        if st.session_state.show_comments.get(post['id'], False):
                            self.load_comments_for_post(post['id'])
                
                # Show comments if expanded
                if st.session_state.show_comments.get(post['id'], False):
                    self._render_comments_for_post(post['id'])
                
                st.markdown("---")
    
    def _render_comments_for_post(self, post_id):
        """Render comments for a specific post"""
        comments = st.session_state.comments.get(post_id, [])
        
        # Comment form
        with st.form(key=f"comment_form_{post_id}"):
            comment_text = st.text_area("Add a comment", key=f"comment_text_{post_id}")
            submit_comment = st.form_submit_button("Post Comment")
            
            if submit_comment and comment_text:
                if self._add_comment(post_id, comment_text):
                    st.success("Comment added!")
                    # Refresh comments
                    self.load_comments_for_post(post_id)
        
        # Display comments
        if not comments:
            st.info("No comments yet. Be the first to comment!")
        else:
            for comment in comments:
                with st.container():
                    col1, col2 = st.columns([1, 5])
                    with col1:
                        if comment['user'].get('profile_picture'):
                            st.image(comment['user']['profile_picture'], width=30)
                        else:
                            st.markdown("👤")
                    
                    with col2:
                        st.markdown(f"**{comment['user']['username']}**: {comment['content']}")
                        
                        # Like comment
                        like_label = "❤️" if comment.get('is_liked') else "🤍"
                        like_count = comment.get('like_count', 0)
                        if st.button(f"{like_label} {like_count}", key=f"like_comment_{comment['id']}"):
                            self._like_comment(comment['id'])
    
    def load_posts_for_spot(self, spot_id):
        """Load posts for a specific tourist spot"""
        if not st.session_state.is_authenticated:
            return
        
        try:
            response = requests.get(
                f"{self.backend_url}/social/posts/spot/{spot_id}",
                headers={"Authorization": f"Bearer {st.session_state.user_token}"}
            )
            
            if response.status_code == 200:
                posts = response.json()
                
                # Convert string dates to datetime objects for sorting
                for post in posts:
                    post['created_at_dt'] = datetime.fromisoformat(post['created_at'].replace('Z', '+00:00'))
                
                # Sort posts by date (newest first)
                posts.sort(key=lambda x: x['created_at_dt'], reverse=True)
                
                st.session_state.posts = posts
            else:
                st.error("Failed to load posts!")
        except Exception as e:
            st.error(f"Error loading posts: {str(e)}")
    
    def load_comments_for_post(self, post_id):
        """Load comments for a specific post"""
        if not st.session_state.is_authenticated:
            return
        
        try:
            response = requests.get(
                f"{self.backend_url}/social/posts/{post_id}/comments",
                headers={"Authorization": f"Bearer {st.session_state.user_token}"}
            )
            
            if response.status_code == 200:
                comments = response.json()
                st.session_state.comments[post_id] = comments
            else:
                st.error("Failed to load comments!")
        except Exception as e:
            st.error(f"Error loading comments: {str(e)}")
    
    def _login_user(self, username, password):
        """Login user and get access token"""
        try:
            response = requests.post(
                f"{self.backend_url}/auth/token",
                data={"username": username, "password": password}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                st.session_state.user_token = token_data["access_token"]
                
                # Get user info
                user_response = requests.get(
                    f"{self.backend_url}/auth/me",
                    headers={"Authorization": f"Bearer {st.session_state.user_token}"}
                )
                
                if user_response.status_code == 200:
                    st.session_state.user_info = user_response.json()
                    st.session_state.is_authenticated = True
                    return True
            else:
                st.error("Invalid username or password!")
                return False
        except Exception as e:
            st.error(f"Login error: {str(e)}")
            return False
    
    def _register_user(self, username, email, full_name, password):
        """Register a new user"""
        try:
            response = requests.post(
                f"{self.backend_url}/auth/register",
                json={
                    "username": username,
                    "email": email,
                    "full_name": full_name,
                    "password": password
                }
            )
            
            if response.status_code == 200:
                return True
            else:
                error_detail = "Registration failed!"
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        error_detail = error_data["detail"]
                except:
                    pass
                st.error(error_detail)
                return False
        except Exception as e:
            st.error(f"Registration error: {str(e)}")
            return False
    
    def _logout_user(self):
        """Logout user"""
        st.session_state.user_token = None
        st.session_state.user_info = None
        st.session_state.is_authenticated = False
        st.session_state.uploaded_media = []
        st.session_state.posts = []
        st.session_state.comments = {}
        st.session_state.show_comments = {}
    
    def _like_post(self, post_id):
        """Like or unlike a post"""
        if not st.session_state.is_authenticated:
            return
        
        try:
            response = requests.post(
                f"{self.backend_url}/social/posts/{post_id}/like",
                headers={"Authorization": f"Bearer {st.session_state.user_token}"}
            )
            
            if response.status_code == 200:
                # Update post in session state
                for i, post in enumerate(st.session_state.posts):
                    if post['id'] == post_id:
                        # Toggle like status
                        post['is_liked'] = not post.get('is_liked', False)
                        # Update like count
                        if post['is_liked']:
                            post['like_count'] = post.get('like_count', 0) + 1
                        else:
                            post['like_count'] = max(0, post.get('like_count', 0) - 1)
                        st.session_state.posts[i] = post
                        break
                
                st.rerun()
            else:
                st.error("Failed to like post!")
        except Exception as e:
            st.error(f"Error liking post: {str(e)}")
    
    def _like_comment(self, comment_id):
        """Like or unlike a comment"""
        if not st.session_state.is_authenticated:
            return
        
        try:
            response = requests.post(
                f"{self.backend_url}/social/comments/{comment_id}/like",
                headers={"Authorization": f"Bearer {st.session_state.user_token}"}
            )
            
            if response.status_code == 200:
                # Update comment in session state
                for post_id, comments in st.session_state.comments.items():
                    for i, comment in enumerate(comments):
                        if comment['id'] == comment_id:
                            # Toggle like status
                            comment['is_liked'] = not comment.get('is_liked', False)
                            # Update like count
                            if comment['is_liked']:
                                comment['like_count'] = comment.get('like_count', 0) + 1
                            else:
                                comment['like_count'] = max(0, comment.get('like_count', 0) - 1)
                            st.session_state.comments[post_id][i] = comment
                            break
                
                st.rerun()
            else:
                st.error("Failed to like comment!")
        except Exception as e:
            st.error(f"Error liking comment: {str(e)}")
    
    def _add_comment(self, post_id, content):
        """Add a comment to a post"""
        if not st.session_state.is_authenticated:
            return False
        
        try:
            response = requests.post(
                f"{self.backend_url}/social/posts/{post_id}/comments",
                headers={"Authorization": f"Bearer {st.session_state.user_token}"},
                data={"content": content}
            )
            
            if response.status_code == 200:
                # Update post comment count
                for i, post in enumerate(st.session_state.posts):
                    if post['id'] == post_id:
                        post['comment_count'] = post.get('comment_count', 0) + 1
                        st.session_state.posts[i] = post
                        break
                
                return True
            else:
                st.error("Failed to add comment!")
                return False
        except Exception as e:
            st.error(f"Error adding comment: {str(e)}")
            return False
