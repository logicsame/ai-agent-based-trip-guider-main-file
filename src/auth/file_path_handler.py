import os
import logging
import glob
from typing import Optional

# Set up logging
logger = logging.getLogger("FilePathHandler")

class FilePathHandler:
    """
    Utility class to handle file path mismatches between database records and actual files.
    Provides methods to find the closest matching file when exact matches aren't found.
    """
    
    @staticmethod
    def get_actual_file_path(base_path: str, requested_path: str) -> Optional[str]:
        """
        Attempts to find the actual file path when there's a mismatch.
        
        Args:
            base_path: The base directory path (e.g., uploads directory)
            requested_path: The path requested by the application
            
        Returns:
            The actual file path if found, or None if no match could be found
        """
        # Remove leading slash if present
        if requested_path.startswith('/'):
            requested_path = requested_path[1:]
            
        # Construct the full path
        full_path = os.path.join(base_path, requested_path)
        
        # Check if the exact file exists
        if os.path.exists(full_path):
            return full_path
            
        # If exact file doesn't exist, try to find a close match
        try:
            # Get the directory and filename
            directory, filename = os.path.split(full_path)
            
            # Check if directory exists
            if not os.path.exists(directory):
                logger.warning(f"Directory does not exist: {directory}")
                return None
                
            # Get the filename without extension and the extension
            name, ext = os.path.splitext(filename)
            
            # Try to find files with similar names in the directory
            pattern = os.path.join(directory, f"{name[:-1]}*{ext}")
            matching_files = glob.glob(pattern)
            
            if matching_files:
                # Sort by similarity to the original filename
                matching_files.sort(key=lambda x: FilePathHandler._similarity_score(filename, os.path.basename(x)))
                best_match = matching_files[0]
                
                logger.info(f"Found close match for {filename}: {os.path.basename(best_match)}")
                return best_match
                
            # If no match found with pattern, list all files in directory
            all_files = os.listdir(directory)
            
            # Filter files with the same extension
            same_ext_files = [f for f in all_files if f.endswith(ext)]
            
            if same_ext_files:
                # Sort by similarity to the original filename
                same_ext_files.sort(key=lambda x: FilePathHandler._similarity_score(filename, x))
                best_match = os.path.join(directory, same_ext_files[0])
                
                logger.info(f"Found alternative match for {filename}: {os.path.basename(best_match)}")
                return best_match
                
            logger.warning(f"No matching file found for {filename} in {directory}")
            return None
            
        except Exception as e:
            logger.error(f"Error finding file match: {str(e)}")
            return None
    
    @staticmethod
    def _similarity_score(original: str, candidate: str) -> int:
        """
        Calculate a similarity score between two filenames.
        Lower score means more similar.
        
        Args:
            original: The original filename
            candidate: The candidate filename to compare
            
        Returns:
            A similarity score (lower is better)
        """
        # Simple implementation using Levenshtein distance
        return FilePathHandler._levenshtein_distance(original, candidate)
    
    @staticmethod
    def _levenshtein_distance(s1: str, s2: str) -> int:
        """
        Calculate the Levenshtein distance between two strings.
        
        Args:
            s1: First string
            s2: Second string
            
        Returns:
            The Levenshtein distance
        """
        if len(s1) < len(s2):
            return FilePathHandler._levenshtein_distance(s2, s1)
            
        if len(s2) == 0:
            return len(s1)
            
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
            
        return previous_row[-1]
