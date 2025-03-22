import os
from dotenv import load_dotenv
from groq import Groq
import time
import logging
from typing import Callable, Any, List, Dict

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("GroqAPIManager")

# Load environment variables
load_dotenv()

class GroqKeyManager:
    def __init__(self):
        """Initialize with multiple API keys from environment variables"""
        # Get the main API key
        self.api_keys = []
        
        # Add the main API key
        main_key = os.getenv("GROQ_API_KEY")
        if main_key:
            self.api_keys.append(main_key)
        
        # Add additional numbered keys
        i = 1
        while True:
            key_name = f"GROQ_API_KEY_{i}"
            key = os.getenv(key_name)
            if key:
                self.api_keys.append(key)
                i += 1
            else:
                break
                
        if not self.api_keys:
            raise ValueError("No Groq API keys found in environment variables")
            
        self.current_index = 0
        self.clients = {key: Groq(api_key=key) for key in self.api_keys}
        logger.info(f"Initialized with {len(self.api_keys)} API keys")
    
    def get_current_key(self):
        """Get the currently active API key"""
        return self.api_keys[self.current_index]
    
    def get_current_client(self):
        """Get the client for the currently active API key"""
        return self.clients[self.get_current_key()]
    
    def rotate_key(self):
        """Rotate to the next API key"""
        old_index = self.current_index
        self.current_index = (self.current_index + 1) % len(self.api_keys)
        logger.info(f"Rotated from key index {old_index} to {self.current_index}")
        return self.get_current_key()
    
    def execute_with_fallback(self, operation: Callable, messages: List[Dict[str, str]], max_retries=3):
        """
        Execute an operation with automatic key rotation on rate limit errors
        
        Args:
            operation: A callable that takes a client and messages and returns a response
            messages: The messages to pass to the operation
            max_retries: Maximum number of retries across all keys
            
        Returns:
            The response from the operation
        """
        attempts = 0
        retry_delay = 1  # Start with 1 second retry delay
        
        while attempts < max_retries * len(self.api_keys):
            current_client = self.get_current_client()
            
            try:
                logger.info(f"Attempting request with key index {self.current_index}")
                return operation(current_client, messages)
                
            except Exception as e:
                attempts += 1
                error_message = str(e).lower()
                
                # Check for rate limit related errors
                if any(phrase in error_message for phrase in ["rate limit", "quota exceeded", "too many requests", "429"]):
                    logger.warning(f"Rate limit hit with key index {self.current_index}: {e}")
                    
                    # If we've tried all keys, implement exponential backoff
                    if attempts % len(self.api_keys) == 0:
                        wait_time = min(retry_delay * 2, 60)  # Cap at 60 seconds
                        logger.info(f"All keys have been tried. Waiting {wait_time}s before retrying...")
                        time.sleep(wait_time)
                        retry_delay *= 2
                    
                    # Rotate to next key
                    self.rotate_key()
                else:
                    # For non-rate-limit errors, just log and re-raise
                    logger.error(f"Non-rate-limit error occurred: {e}")
                    raise
        
        # If we've exhausted all retries
        raise Exception(f"Failed after {attempts} attempts across {len(self.api_keys)} API keys")
