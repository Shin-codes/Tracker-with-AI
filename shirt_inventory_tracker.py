import json
import os
from typing import List, Dict, Optional


# Constants for allowed statuses. These drive validation and menu choices.
STATUSES: List[str] = [
    "In Drawer",
    "Laundry",
    "Worn",
]


def get_data_file_path() -> str:
    """Return an absolute path to the JSON data file stored next to this script."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "shirts_data.json")


def load_data() -> List[Dict]:
    """
    Load shirts from the JSON file. If the file does not exist or is invalid,
    return an empty list. Each shirt is a dict with keys: id, name, color, size, status.
    """
    data_file = get_data_file_path()
    if not os.path.exists(data_file):
        return []
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except (json.JSONDecodeError, OSError):
        # If the file is corrupted or unreadable, start fresh.
        return []


def save_data(shirts: List[Dict]) -> None:
    """Persist shirts to the JSON file in a readable format."""
    data_file = get_data_file_path()
    try:
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(shirts, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"Error saving data: {e}")


def generate_next_id(shirts: List[Dict]) -> int:
    """Generate a unique integer ID based on the current list contents."""
    if not shirts:
        return 1
    # IDs are positive integers; choose 1 + max existing id
    return max((s.get("id", 0) for s in shirts), default=0) + 1


# ----- Input Helpers -----

def prompt_non_empty(prompt_text: str) -> str:
    """Prompt until the user enters a non-empty string (trimmed)."""
    while True:
        value = input(prompt_text).strip()
        if value:
            return value
        print("Input cannot be empty. Please try again.")


def prompt_choice_from_list(prompt_text: str, choices: List[str]) -> str:
    """
    Present a numbered menu for choices and return the selected string.
    Handles invalid numeric inputs gracefully.
    """
    if not choices:
        raise ValueError("No choices provided")

    while True:
        print(prompt_text)
        for idx, choice in enumerate(choices, start=1):
            print(f"  {idx}. {choice}")
        raw = input("Enter choice number: ").strip()
        if not raw.isdigit():
            print("Please enter a valid number.")
            continue
        num = int(raw)
        if 1 <= num <= len(choices):
            return choices[num - 1]
        print("Choice out of range. Please try again.")


def prompt_int(prompt_text: str) -> Optional[int]:
    """Prompt for an integer. Returns None if the user inputs nothing."""
    raw = input(prompt_text).strip()
    if raw == "":
        return None
    if raw.lstrip("-+").isdigit():
        return int(raw)
    print("Please enter a valid integer.")
    return None


# ----- Core Operations -----

def add_shirt(shirts: List[Dict]) -> None:
    """Add a new shirt with validated fields and persist the change."""
    print("\nAdd a New Shirt")
    name = prompt_non_empty("Name: ")
    color = prompt_non_empty("Color: ")
    size = prompt_non_empty("Size: ")
    status = prompt_choice_from_list("Select status:", STATUSES)

    new_shirt = {
        "id": generate_next_id(shirts),
        "name": name,
        "color": color,
        "size": size,
        "status": status,
    }
    shirts.append(new_shirt)
    save_data(shirts)
    print(f"Added shirt #{new_shirt['id']} - {name} ({color}, {size}) [{status}]")


def display_counts(shirts: List[Dict]) -> None:
    """Display counts for each status and total."""
    counts = {status: 0 for status in STATUSES}
    for s in shirts:
        status = s.get("status")
        if status in counts:
            counts[status] += 1
    total = len(shirts)
    print("\nShirt Counts:")
    for status in STATUSES:
        print(f"  {status}: {counts[status]}")
    print(f"  Total: {total}")


def display_shirts_grouped(shirts: List[Dict]) -> None:
    """Print all shirts grouped by status. Handles empty lists."""
    print("\nView Shirts (Grouped by Status)")
    if not shirts:
        print("No shirts found. Add some shirts first.")
        return

    # Group shirts by status preserving the STATUSES order
    groups = {status: [] for status in STATUSES}
    for s in shirts:
        status = s.get("status")
        if status in groups:
            groups[status].append(s)
        else:
            # Handle any legacy/invalid statuses gracefully
            groups.setdefault(status or "Unknown", []).append(s)

    for status in STATUSES:
        items = groups.get(status, [])
        print(f"\n[{status}] ({len(items)})")
        if not items:
            print("  - None -")
        else:
            for s in items:
                print(
                    f"  #{s['id']}: {s['name']} | Color: {s['color']} | Size: {s['size']}"
                )

    # Bonus counts view
    display_counts(shirts)


def select_shirt_by_id(shirts: List[Dict]) -> Optional[Dict]:
    """
    List shirts with their IDs and prompt the user to select one by id.
    Returns the shirt dict or None if not found/aborted.
    """
    if not shirts:
        print("No shirts available.")
        return None

    print("\nAvailable Shirts:")
    for s in shirts:
        print(
            f"  #{s['id']}: {s['name']} | {s['color']} | {s['size']} | {s['status']}"
        )

    while True:
        selected_id = prompt_int("Enter shirt ID (or press Enter to cancel): ")
        if selected_id is None:
            print("Cancelled.")
            return None
        for s in shirts:
            if s.get("id") == selected_id:
                return s
        print("No shirt with that ID. Please try again.")


def update_shirt_status(shirts: List[Dict]) -> None:
    """Update the status of a selected shirt and persist the change."""
    print("\nUpdate Shirt Status")
    shirt = select_shirt_by_id(shirts)
    if not shirt:
        return
    current_status = shirt.get("status")
    print(f"Current status: {current_status}")
    new_status = prompt_choice_from_list("Select new status:", STATUSES)
    if new_status == current_status:
        print("Status unchanged.")
        return
    shirt["status"] = new_status
    save_data(shirts)
    print(
        f"Updated shirt #{shirt['id']} - {shirt['name']} to status [{new_status}]"
    )


def delete_shirt(shirts: List[Dict]) -> None:
    """Delete a selected shirt by id and persist the change."""
    print("\nDelete a Shirt")
    shirt = select_shirt_by_id(shirts)
    if not shirt:
        return
    confirm = input(
        f"Are you sure you want to delete '#{shirt['id']} - {shirt['name']}'? (y/N): "
    ).strip().lower()
    if confirm == "y":
        shirts.remove(shirt)
        save_data(shirts)
        print("Shirt deleted.")
    else:
        print("Deletion cancelled.")


# ----- CLI Menu -----

def print_menu() -> None:
    """Display the main menu options."""
    print("\nShirt Inventory Tracker")
    print("-----------------------")
    print("1) Add a shirt")
    print("2) View all shirts (grouped)")
    print("3) Update shirt status")
    print("4) Delete a shirt")
    print("5) Show counts")
    print("0) Exit")


def main() -> None:
    """
    Entry point for the CLI application. Loads data once, ensures persistence
    after each modification, and handles invalid inputs gracefully.
    """
    shirts: List[Dict] = load_data()

    while True:
        print_menu()
        choice = input("Select an option: ").strip()

        if choice == "1":
            add_shirt(shirts)
        elif choice == "2":
            display_shirts_grouped(shirts)
        elif choice == "3":
            update_shirt_status(shirts)
        elif choice == "4":
            delete_shirt(shirts)
        elif choice == "5":
            display_counts(shirts)
        elif choice == "0":
            # Save on exit just in case
            save_data(shirts)
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please choose a number from the menu.")


if __name__ == "__main__":
    main()


