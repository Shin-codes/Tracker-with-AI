"""Utilities for managing shirt images."""
import os
import shutil
from typing import Optional
from pathlib import Path


def get_images_dir() -> str:
    """Get the path to the images directory, creating it if needed."""
    src_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(src_dir)
    images_dir = os.path.join(root_dir, "data", "images")
    os.makedirs(images_dir, exist_ok=True)
    return images_dir


def get_image_path(shirt_id: int, filename: Optional[str] = None) -> str:
    """Get the full path for a shirt's image."""
    images_dir = get_images_dir()
    if filename:
        # Use provided filename
        return os.path.join(images_dir, filename)
    # Default: shirt_{id}.jpg
    return os.path.join(images_dir, f"shirt_{shirt_id}.jpg")


def save_image_from_path(src_path: str, shirt_id: int, original_filename: Optional[str] = None) -> str:
    """Copy an image file to the images directory for a shirt.
    
    Args:
        src_path: Path to source image file
        shirt_id: ID of the shirt
        original_filename: Optional original filename to preserve extension
    
    Returns:
        Relative path to saved image (from data/images/)
    """
    if not os.path.exists(src_path):
        raise FileNotFoundError(f"Image file not found: {src_path}")
    
    # Determine extension
    if original_filename:
        ext = Path(original_filename).suffix.lower()
    else:
        ext = Path(src_path).suffix.lower()
    
    if not ext:
        ext = ".jpg"  # Default
    
    # Generate destination filename
    filename = f"shirt_{shirt_id}{ext}"
    dest_path = get_image_path(shirt_id, filename)
    
    # Copy file
    shutil.copy2(src_path, dest_path)
    
    # Return relative path
    images_dir = get_images_dir()
    return os.path.join("images", filename)


def delete_image(image_path: str) -> None:
    """Delete an image file if it exists."""
    if not image_path:
        return
    
    src_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(src_dir)
    full_path = os.path.join(root_dir, "data", image_path)
    
    if os.path.exists(full_path):
        try:
            os.remove(full_path)
        except OSError:
            pass  # Ignore errors on deletion


def get_image_display_path(image_path: str) -> Optional[str]:
    """Get full path to image for display, or None if not found."""
    if not image_path:
        return None
    
    src_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(src_dir)
    full_path = os.path.join(root_dir, "data", image_path)
    
    if os.path.exists(full_path):
        return full_path
    return None

