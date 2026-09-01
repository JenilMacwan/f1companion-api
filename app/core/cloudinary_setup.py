"""
Cloudinary integration for image asset management.
"""

import os
import cloudinary
import cloudinary.uploader
import cloudinary.api

def initialize_cloudinary():
    """
    Initialize Cloudinary using the CLOUDINARY_URL environment variable.
    """
    cloudinary_url = os.getenv("CLOUDINARY_URL")
    if cloudinary_url:
        # Cloudinary automatically picks up the CLOUDINARY_URL environment variable
        # when you configure it without passing explicit credentials.
        cloudinary.config()
        print("Cloudinary initialized successfully.")
    else:
        print("Warning: CLOUDINARY_URL environment variable not set. Image uploads/fetching via Cloudinary will not work.")

def get_image_url(public_id: str, **kwargs) -> str:
    """
    Generate a Cloudinary URL for a specific image asset.
    
    Args:
        public_id (str): The public ID of the image in Cloudinary (e.g., 'banner').
        **kwargs: Additional transformation arguments (e.g., width=1200, height=630, crop='fill').
        
    Returns:
        str: The fully qualified Cloudinary image URL.
    """
    url, _ = cloudinary.utils.cloudinary_url(public_id, **kwargs)
    return url
