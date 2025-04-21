"""URL utilities for handling path concatenation properly."""

def join_url_paths(base_url, path):
    """
    Join a base URL and a path, ensuring there are no double slashes.
    
    Args:
        base_url (str): The base URL (e.g., "http://127.0.0.1:8000")
        path (str): The path to append (e.g., "/uploads/image.jpg")
        
    Returns:
        str: Properly joined URL without double slashes
    """
    if not path:
        return base_url
        
    # If path already has a protocol, return it as is
    if path.startswith(('http://', 'https://')):
        return path
        
    # Remove trailing slash from base_url if present
    if base_url.endswith('/'):
        base_url = base_url[:-1]
        
    # Remove leading slash from path if present
    if path.startswith('/'):
        path = path[1:]
        
    # Join with a single slash
    return f"{base_url}/{path}"
