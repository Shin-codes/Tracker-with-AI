from typing import List, Dict

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


