from dataclasses import dataclass, asdict
from typing import List, Dict, Any


STATUSES: List[str] = [
    "In Drawer",
    "Laundry",
    "Worn",
]


@dataclass
class Shirt:
    id: int
    name: str
    color: str
    size: str
    status: str
    image_path: str = ""  # Path to image file (relative to data/images/)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Shirt":
        return Shirt(
            id=int(data.get("id", 0)),
            name=str(data.get("name", "")).strip(),
            color=str(data.get("color", "")).strip(),
            size=str(data.get("size", "")).strip(),
            status=str(data.get("status", "")).strip() or STATUSES[0],
            image_path=str(data.get("image_path", "")).strip(),
        )


