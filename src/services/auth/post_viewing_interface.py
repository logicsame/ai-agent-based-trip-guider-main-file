import streamlit as st
import requests
from datetime import datetime
import time
import io
from PIL import Image
import base64
from .url_utils import join_url_paths

class PostViewingInterface:
    def __init__(self, social_interface, backend_url="http://127.0.0.1:8000"):
        self.social_interface = social_interface
        self.backend_url = backend_url
        
        # Initialize session state variables for post viewing
        if 'post_filter' not in st.session_state:
            st.session_state.post_filter = "newest"
        if 'expanded_post' not in st.session_state:
            st.session_state.expanded_post = None
        if 'media_view' not in st.session_state:
            st.session_state.media_view = None
    
    def render_post_filters(self):
        """Render filters for posts"""
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            filter_option = st.selectbox(
                "Sort by", 
                ["Newest", "Most Liked", "Most Commented"],
                index=0 if st.session_state.post_filter == "newest" else 
                      1 if st.session_state.post_filter == "likes" else 2
            )
            
            # Update filter in session state
            if filter_option == "Newest":
                st.session_state.post_filter = "newest"
            elif filter_option == "Most Liked":
                st.session_state.post_filter = "likes"
            else:
                st.session_state.post_filter = "comments"
        
        with col2:
            refresh_button = st.button("🔄 Refresh", use_container_width=True)
            if refresh_button:
                # Clear posts to force reload
                st.session_state.posts = []
                st.rerun()
    
    def render_posts(self, spot_id, context="spot"):
        """Render posts for a specific tourist spot with enhanced UI
        
        Args:
            spot_id: ID of the spot to show posts for
            context: Context identifier for unique keys (e.g., "spot", "user", "trending")
        """
        if not st.session_state.is_authenticated:
            st.warning("Please login to view posts!")
            return
        
        # Always reload posts when spot_id changes to ensure we're showing the correct posts
        # Store current spot_id in session state to detect changes
        if 'current_spot_id' not in st.session_state:
            st.session_state.current_spot_id = None
            
        # If spot_id changed or posts not loaded, reload posts
        if st.session_state.current_spot_id != spot_id or not st.session_state.posts:
            # Clear existing posts
            st.session_state.posts = []
            # Update current spot_id
            st.session_state.current_spot_id = spot_id
            # Load posts for this spot
            self.social_interface.load_posts_for_spot(spot_id)
        
        # Apply filters to posts
        posts = self._filter_posts(st.session_state.posts)
        
        if not posts:
            st.info("No posts yet for this spot. Be the first to share your experience!")
            return
        
        # Render post filters
        self.render_post_filters()
        
        # Render each post
        for post in posts:
            self._render_post_card(post, context)
    
    def _filter_posts(self, posts):
        """Filter and sort posts based on selected filter"""
        if not posts:
            return []
        
        filtered_posts = posts.copy()
        
        # Sort based on filter
        if st.session_state.post_filter == "newest":
            filtered_posts.sort(key=lambda x: x.get('created_at_dt', datetime.now()), reverse=True)
        elif st.session_state.post_filter == "likes":
            filtered_posts.sort(key=lambda x: x.get('like_count', 0), reverse=True)
        elif st.session_state.post_filter == "comments":
            filtered_posts.sort(key=lambda x: x.get('comment_count', 0), reverse=True)
        
        return filtered_posts
    
    def _render_post_card(self, post, context="spot"):
        """Render a single post card with enhanced UI
        
        Args:
            post: Post data to render
            context: Context identifier for unique keys (e.g., "spot", "user", "trending")
        """
        is_expanded = st.session_state.expanded_post == post['id']
        
        with st.container():
            # Post header
            col1, col2, col3 = st.columns([1, 4, 1])
            
            with col1:
                if post['user'].get('profile_picture'):
                    profile_pic_url = join_url_paths(self.backend_url, post['user']['profile_picture'])
                    st.image(profile_pic_url, width=60)
                else:
                    st.markdown("👤")
            
            with col2:
                st.markdown(f"### {post['title']}")
                st.markdown(f"**{post['user']['full_name']}** (@{post['user']['username']})")
                st.markdown(f"*{post['created_at'].split('T')[0]}*")
            
            with col3:
                if st.button("Expand" if not is_expanded else "Collapse", key=f"{context}_expand_{post['id']}"):
                    if is_expanded:
                        st.session_state.expanded_post = None
                    else:
                        st.session_state.expanded_post = post['id']
                    st.rerun()
            
            # Post content (always visible)
            st.markdown(post['content'])
            
            # Media gallery (always visible but compact if not expanded)
            if post.get('media') and len(post['media']) > 0:
                media_items = post['media']
                
                if not is_expanded and len(media_items) > 0:
                    # Show only first media item if not expanded
                    media = media_items[0]
                    if media['type'] == 'image':
                        # Use the URL utility to properly join paths
                        media_url = join_url_paths(self.backend_url, media['url'])
                        st.image(media_url, use_container_width=True)
                    elif media['type'] == 'video':
                        # Use the URL utility to properly join paths
                        media_url = join_url_paths(self.backend_url, media['url'])
                        st.video(media_url)
                    
                    if len(media_items) > 1:
                        st.markdown(f"*+{len(media_items)-1} more media items*")
                elif is_expanded:
                    # Show all media items in a grid if expanded
                    cols = st.columns(min(3, len(media_items)))
                    
                    for i, media in enumerate(media_items):
                        col_idx = i % len(cols)
                        with cols[col_idx]:
                            if media['type'] == 'image':
                                # Make image clickable for full view
                                if st.button("View Full Size", key=f"{context}_view_{post['id']}_{i}"):
                                    # Use the URL utility to properly join paths
                                    media_url = join_url_paths(self.backend_url, media['url'])
                                    
                                    st.session_state.media_view = {
                                        'url': media_url,
                                        'type': 'image',
                                        'caption': media.get('caption', '')
                                    }
                                    st.rerun()
                                
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
            
            # Action buttons
            col1, col2, col3 = st.columns([1, 1, 5])
            with col1:
                like_label = "❤️" if post.get('is_liked') else "🤍"
                like_count = post.get('like_count', 0)
                if st.button(f"{like_label} {like_count}", key=f"like_{post['id']}"):
                    self.social_interface._like_post(post['id'])
            
            with col2:
                comment_count = post.get('comment_count', 0)
                if st.button(f"💬 {comment_count}", key=f"comment_{post['id']}"):
                    # Toggle comments visibility
                    st.session_state.show_comments[post['id']] = not st.session_state.show_comments.get(post['id'], False)
                    
                    # Load comments if showing
                    if st.session_state.show_comments.get(post['id'], False):
                        self.social_interface.load_comments_for_post(post['id'])
                        
                        # If expanded, scroll to comments
                        if is_expanded:
                            st.rerun()
            
            # Show comments if expanded or comments button clicked
            if is_expanded or st.session_state.show_comments.get(post['id'], False):
                self._render_enhanced_comments(post['id'])
            
            st.markdown("---")
    
    def _render_enhanced_comments(self, post_id):
        """Render enhanced comments section for a post"""
        comments = st.session_state.comments.get(post_id, [])
        
        # Comment form with improved UI
        with st.container():
            st.markdown("### Add a comment")
            
            comment_text = st.text_area("", placeholder="Write your comment here...", key=f"comment_text_{post_id}")
            
            col1, col2 = st.columns([1, 5])
            with col1:
                if st.button("Post Comment", key=f"post_comment_{post_id}"):
                    if comment_text:
                        if self.social_interface._add_comment(post_id, comment_text):
                            st.success("Comment added!")
                            # Clear comment text
                            st.session_state[f"comment_text_{post_id}"] = ""
                            # Refresh comments
                            self.social_interface.load_comments_for_post(post_id)
                            st.rerun()
                    else:
                        st.warning("Please enter a comment")
        
        # Display comments with improved UI
        if not comments:
            st.info("No comments yet. Be the first to comment!")
        else:
            st.markdown("### Comments")
            
            for comment in comments:
                with st.container():
                    col1, col2 = st.columns([1, 6])
                    
                    with col1:
                        if comment['user'].get('profile_picture'):
                            st.image(f"{self.backend_url}{comment['user']['profile_picture']}", width=50)
                        else:
                            st.markdown("👤")
                    
                    with col2:
                        st.markdown(f"**{comment['user']['full_name']}** (@{comment['user']['username']})")
                        st.markdown(f"*{comment['created_at'].split('T')[0]}*")
                        st.markdown(comment['content'])
                        
                        # Like comment button
                        like_label = "❤️" if comment.get('is_liked') else "🤍"
                        like_count = comment.get('like_count', 0)
                        if st.button(f"{like_label} {like_count}", key=f"like_comment_{comment['id']}"):
                            self.social_interface._like_comment(comment['id'])
                            st.rerun()
                    
                    st.markdown("---")
    
    def render_media_viewer(self):
        """Render full-size media viewer"""
        if st.session_state.media_view:
            with st.container():
                st.markdown("### Media Viewer")
                
                # Close button
                if st.button("Close Viewer"):
                    st.session_state.media_view = None
                    st.rerun()
                
                # Display media
                media = st.session_state.media_view
                if media['type'] == 'image':
                    st.image(media['url'], use_column_width=True)
                elif media['type'] == 'video':
                    st.video(media['url'])
                
                # Caption
                if media.get('caption'):
                    st.markdown(f"*{media['caption']}*")
    
    def render_user_posts(self, user_id=None):
        """Render posts by a specific user or the current user"""
        if not st.session_state.is_authenticated:
            st.warning("Please login to view posts!")
            return
        
        # Use current user if no user_id provided
        if not user_id and st.session_state.user_info:
            user_id = st.session_state.user_info.get('id')
        
        if not user_id:
            st.warning("User not found!")
            return
        
        # Load user posts
        try:
            response = requests.get(
                f"{self.backend_url}/social/posts/user/{user_id}",
                headers={"Authorization": f"Bearer {st.session_state.user_token}"}
            )
            
            if response.status_code == 200:
                posts = response.json()
                
                # Convert string dates to datetime objects for sorting
                for post in posts:
                    post['created_at_dt'] = datetime.fromisoformat(post['created_at'].replace('Z', '+00:00'))
                
                # Sort posts by date (newest first)
                posts.sort(key=lambda x: x['created_at_dt'], reverse=True)
                
                if not posts:
                    st.info("No posts yet.")
                    return
                
                st.markdown("### My Posts")
                
                # Render each post
                for post in posts:
                    self._render_post_card(post)
            else:
                st.error("Failed to load user posts!")
        except Exception as e:
            st.error(f"Error loading user posts: {str(e)}")
    
    def render_trending_posts(self, limit=5):
        """Render trending posts across all tourist spots"""
        if not st.session_state.is_authenticated:
            st.warning("Please login to view trending posts!")
            return
        
        try:
            response = requests.get(
                f"{self.backend_url}/social/posts/trending?limit={limit}",
                headers={"Authorization": f"Bearer {st.session_state.user_token}"}
            )
            
            if response.status_code == 200:
                posts = response.json()
                
                if not posts:
                    st.info("No trending posts available.")
                    return
                
                st.markdown("### Trending Posts")
                
                # Render each post
                for post in posts:
                    with st.container():
                        st.markdown(f"### {post['title']}")
                        st.markdown(f"**Location:** {post['spot_name']}")
                        
                        col1, col2 = st.columns([1, 5])
                        with col1:
                            if post['user'].get('profile_picture'):
                                st.image(f"{self.backend_url}{post['user']['profile_picture']}", width=50)
                            else:
                                st.markdown("👤")
                        
                        with col2:
                            st.markdown(f"**{post['user']['full_name']}** (@{post['user']['username']})")
                            st.markdown(f"*{post['created_at'].split('T')[0]}*")
                        
                        # Post content preview
                        content_preview = post['content'][:200] + "..." if len(post['content']) > 200 else post['content']
                        st.markdown(content_preview)
                        
                        # View button
                        if st.button("View Full Post", key=f"view_trending_{post['id']}"):
                            # Store spot ID to navigate to
                            st.session_state.navigate_to_spot = post['spot_id']
                            st.session_state.navigate_to_post = post['id']
                            st.rerun()
                        
                        st.markdown("---")
            else:
                st.error("Failed to load trending posts!")
        except Exception as e:
            st.error(f"Error loading trending posts: {str(e)}")
