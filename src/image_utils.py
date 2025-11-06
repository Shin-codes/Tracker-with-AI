"""Utilities for managing shirt images."""
import os
import shutil
from typing import Optional, Tuple, List
from pathlib import Path
from collections import Counter

from PIL import Image


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


# --- Color analysis helpers ---

def _is_near_white(rgb: Tuple[int, int, int], threshold: int = 240) -> bool:
    """Return True if the color is near white based on a channel threshold."""
    r, g, b = rgb
    return r >= threshold and g >= threshold and b >= threshold


def detect_dominant_color(image_path: str) -> Tuple[int, int, int]:
    """Detect the dominant RGB color in an image while ignoring near-white backgrounds.

    The algorithm downsamples the image for performance, filters out near-white
    pixels, then returns the most frequent remaining color. If filtering removes
    all pixels, it falls back to the most frequent color overall.

    Args:
        image_path: Path to the image to analyze.

    Returns:
        A tuple of (r, g, b) representing the dominant color.
    """
    if not image_path or not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    with Image.open(image_path) as img:
        img = img.convert("RGB")
        # Downsample to reduce noise and speed up counting
        img.thumbnail((150, 150), Image.Resampling.LANCZOS)
        pixels = list(img.getdata())

    # Filter out near-white background
    filtered = [p for p in pixels if not _is_near_white(p)]

    def most_common_color(colors: list[Tuple[int, int, int]]) -> Tuple[int, int, int]:
        if not colors:
            # Should not happen, but guard anyway
            return (255, 255, 255)
        counter = Counter(colors)
        return counter.most_common(1)[0][0]

    if filtered:
        return most_common_color(filtered)
    # Fallback: use most common overall if everything was near white
    return most_common_color(pixels)


def rgb_string(rgb: Tuple[int, int, int]) -> str:
    """Format an (r, g, b) tuple as an rgb() string."""
    r, g, b = rgb
    return f"rgb({r}, {g}, {b})"


# Basic named color palette (approximate RGB centers)
_BASIC_COLORS: List[Tuple[str, Tuple[int, int, int]]] = [
    ("black", (0, 0, 0)),
    ("white", (255, 255, 255)),
    ("gray", (128, 128, 128)),
    ("red", (220, 20, 60)),
    ("orange", (255, 140, 0)),
    ("yellow", (255, 215, 0)),
    ("green", (34, 139, 34)),
    ("teal", (0, 128, 128)),
    ("blue", (30, 144, 255)),
    ("purple", (138, 43, 226)),
    ("pink", (255, 105, 180)),
    ("brown", (139, 69, 19)),
]


def _distance_sq(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> int:
    ar, ag, ab = a
    br, bg, bb = b
    return (ar - br) ** 2 + (ag - bg) ** 2 + (ab - bb) ** 2


def map_rgb_to_basic_color(rgb: Tuple[int, int, int]) -> str:
    """Map an RGB color to a general named color using nearest neighbor.

    Returns a lowercase color name like "red", "green", etc.
    """
    # Special-case near white and near black
    if _is_near_white(rgb, threshold=240):
        return "white"
    if rgb[0] < 20 and rgb[1] < 20 and rgb[2] < 20:
        return "black"

    best_name = "gray"
    best_d = 1_000_000_000
    for name, center in _BASIC_COLORS:
        d = _distance_sq(rgb, center)
        if d < best_d:
            best_d = d
            best_name = name
    return best_name

