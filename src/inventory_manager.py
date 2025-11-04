from typing import List, Dict, Any

from .models import Shirt, STATUSES


def generate_next_id(shirts: List[Shirt]) -> int:
    if not shirts:
        return 1
    return max((s.id for s in shirts), default=0) + 1


def add_shirt(shirts: List[Shirt], name: str, color: str, size: str, status: str) -> Shirt:
    if not name.strip() or not color.strip() or not size.strip():
        raise ValueError("Name, color, and size are required.")
    if status not in STATUSES:
        raise ValueError("Invalid status.")
    shirt = Shirt(
        id=generate_next_id(shirts),
        name=name.strip(),
        color=color.strip(),
        size=size.strip(),
        status=status,
    )
    shirts.append(shirt)
    return shirt


def counts_by_status(shirts: List[Shirt]) -> Dict[str, int]:
    counts = {st: 0 for st in STATUSES}
    for s in shirts:
        if s.status in counts:
            counts[s.status] += 1
    return counts


def grouped_by_status(shirts: List[Shirt]) -> Dict[str, List[Shirt]]:
    groups = {st: [] for st in STATUSES}
    for s in shirts:
        groups.setdefault(s.status, []).append(s)
    return groups


def view_grouped_inventory(shirts: List[Shirt]) -> Dict[str, List[Dict]]:
    """Alias returning plain dicts for easier printing/serialization."""
    groups = grouped_by_status(shirts)
    return {
        status: [
            {
                "id": s.id,
                "name": s.name,
                "color": s.color,
                "size": s.size,
                "status": s.status,
                "image_path": s.image_path,
            }
            for s in items
        ]
        for status, items in groups.items()
    }


def find_by_id(shirts: List[Shirt], shirt_id: int) -> Shirt | None:
    for s in shirts:
        if s.id == shirt_id:
            return s
    return None


def update_status(shirts: List[Shirt], shirt_id: int, new_status: str) -> Shirt:
    if new_status not in STATUSES:
        raise ValueError("Invalid status.")
    s = find_by_id(shirts, shirt_id)
    if not s:
        raise ValueError("Shirt not found.")
    s.status = new_status
    return s


def delete_shirt(shirts: List[Shirt], shirt_id: int) -> None:
    s = find_by_id(shirts, shirt_id)
    if not s:
        raise ValueError("Shirt not found.")
    shirts.remove(s)


def count_by_status(shirts: List[Shirt]) -> Dict[str, int]:
    """Alias for counts_by_status with expected name."""
    return counts_by_status(shirts)


def update_shirt(shirts: List[Shirt], shirt_id: int, name: str = None, color: str = None, 
                 size: str = None, status: str = None, image_path: str = None) -> Shirt:
    """Update shirt properties. Only provided fields will be updated."""
    s = find_by_id(shirts, shirt_id)
    if not s:
        raise ValueError("Shirt not found.")
    
    if name is not None:
        if not name.strip():
            raise ValueError("Name cannot be empty.")
        s.name = name.strip()
    
    if color is not None:
        if not color.strip():
            raise ValueError("Color cannot be empty.")
        s.color = color.strip()
    
    if size is not None:
        if not size.strip():
            raise ValueError("Size cannot be empty.")
        s.size = size.strip()
    
    if status is not None:
        if status not in STATUSES:
            raise ValueError("Invalid status.")
        s.status = status
    
    if image_path is not None:
        s.image_path = image_path.strip() if image_path else ""
    
    return s


def search_shirts(shirts: List[Shirt], query: str) -> List[Shirt]:
    """Search shirts by name, color, size, or status (case-insensitive)."""
    if not query:
        return shirts
    
    query_lower = query.lower().strip()
    results = []
    
    for s in shirts:
        if (query_lower in s.name.lower() or 
            query_lower in s.color.lower() or 
            query_lower in s.size.lower() or 
            query_lower in s.status.lower()):
            results.append(s)
    
    return results


def get_statistics(shirts: List[Shirt]) -> Dict[str, Any]:
    """Get comprehensive statistics about the inventory."""
    if not shirts:
        return {
            "total": 0,
            "by_status": {},
            "by_color": {},
            "by_size": {},
            "with_images": 0,
        }
    
    stats = {
        "total": len(shirts),
        "by_status": counts_by_status(shirts),
        "by_color": {},
        "by_size": {},
        "with_images": 0,
    }
    
    for s in shirts:
        # Count by color
        stats["by_color"][s.color] = stats["by_color"].get(s.color, 0) + 1
        
        # Count by size
        stats["by_size"][s.size] = stats["by_size"].get(s.size, 0) + 1
        
        # Count with images
        if s.image_path:
            stats["with_images"] += 1
    
    return stats


