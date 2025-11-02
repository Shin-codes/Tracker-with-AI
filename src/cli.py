from typing import List

from .models import Shirt, STATUSES
from .storage import load_shirts, save_shirts
from .inventory_manager import (
    add_shirt,
    grouped_by_status,
    update_status,
    update_shirt,
    delete_shirt,
    counts_by_status,
    search_shirts,
    get_statistics,
)


def _prompt_non_empty(prompt_text: str) -> str:
    while True:
        value = input(prompt_text).strip()
        if value:
            return value
        print("Input cannot be empty. Please try again.")


def _prompt_choice(prompt_text: str, choices: List[str]) -> str:
    while True:
        print(prompt_text)
        for i, c in enumerate(choices, start=1):
            print(f"  {i}. {c}")
        raw = input("Enter choice number: ").strip()
        if raw.isdigit():
            idx = int(raw)
            if 1 <= idx <= len(choices):
                return choices[idx - 1]
        print("Invalid choice. Try again.")


def _prompt_int(prompt_text: str) -> int | None:
    raw = input(prompt_text).strip()
    if raw == "":
        return None
    if raw.lstrip("-+").isdigit():
        return int(raw)
    print("Please enter a valid integer.")
    return None


def print_menu() -> None:
    print("\nShirt Inventory Tracker")
    print("-----------------------")
    print("1) Add a shirt")
    print("2) View all shirts (grouped)")
    print("3) Update shirt status")
    print("4) Edit shirt details")
    print("5) Delete a shirt")
    print("6) Search shirts")
    print("7) Show counts")
    print("8) Show statistics")
    print("0) Exit")


def run() -> None:
    shirts: List[Shirt] = load_shirts()

    while True:
        print_menu()
        choice = input("Select an option: ").strip()

        if choice == "1":
            name = _prompt_non_empty("Name: ")
            color = _prompt_non_empty("Color: ")
            size = _prompt_non_empty("Size: ")
            status = _prompt_choice("Select status:", STATUSES)
            try:
                s = add_shirt(shirts, name, color, size, status)
                save_shirts(shirts)
                print(f"Added shirt #{s.id} - {s.name} ({s.color}, {s.size}) [{s.status}]")
            except ValueError as e:
                print(f"Error: {e}")

        elif choice == "2":
            groups = grouped_by_status(shirts)
            if not shirts:
                print("No shirts found. Add some shirts first.")
            else:
                for status in STATUSES:
                    items = groups.get(status, [])
                    print(f"\n[{status}] ({len(items)})")
                    if not items:
                        print("  - None -")
                    else:
                        for s in items:
                            img_indicator = " [📷]" if s.image_path else ""
                            print(
                                f"  #{s.id}: {s.name} | Color: {s.color} | Size: {s.size}{img_indicator}"
                            )

        elif choice == "3":
            if not shirts:
                print("No shirts available.")
                continue
            for s in shirts:
                img_indicator = " [📷]" if s.image_path else ""
                print(f"  #{s.id}: {s.name} | {s.color} | {s.size} | {s.status}{img_indicator}")
            sel = _prompt_int("Enter shirt ID (or press Enter to cancel): ")
            if sel is None:
                print("Cancelled.")
                continue
            new_status = _prompt_choice("Select new status:", STATUSES)
            try:
                s = update_status(shirts, sel, new_status)
                save_shirts(shirts)
                print(f"Updated #{s.id} - {s.name} to [{s.status}]")
            except ValueError as e:
                print(f"Error: {e}")

        elif choice == "4":
            if not shirts:
                print("No shirts available.")
                continue
            for s in shirts:
                img_indicator = " [📷]" if s.image_path else ""
                print(f"  #{s.id}: {s.name} | {s.color} | {s.size} | {s.status}{img_indicator}")
            sel = _prompt_int("Enter shirt ID (or press Enter to cancel): ")
            if sel is None:
                print("Cancelled.")
                continue
            try:
                shirt = [s for s in shirts if s.id == sel][0]
                print(f"\nEditing: #{shirt.id} - {shirt.name}")
                name = input(f"Name [{shirt.name}]: ").strip() or shirt.name
                color = input(f"Color [{shirt.color}]: ").strip() or shirt.color
                size = input(f"Size [{shirt.size}]: ").strip() or shirt.size
                status = _prompt_choice(f"Status (current: {shirt.status}):", STATUSES)
                update_shirt(shirts, sel, name=name, color=color, size=size, status=status)
                save_shirts(shirts)
                print(f"Updated shirt #{sel}.")
            except (ValueError, IndexError) as e:
                print(f"Error: {e}")

        elif choice == "5":
            if not shirts:
                print("No shirts available.")
                continue
            for s in shirts:
                img_indicator = " [📷]" if s.image_path else ""
                print(f"  #{s.id}: {s.name} | {s.color} | {s.size} | {s.status}{img_indicator}")
            sel = _prompt_int("Enter shirt ID (or press Enter to cancel): ")
            if sel is None:
                print("Cancelled.")
                continue
            try:
                delete_shirt(shirts, sel)
                save_shirts(shirts)
                print("Shirt deleted.")
            except ValueError as e:
                print(f"Error: {e}")

        elif choice == "6":
            query = input("Enter search query: ").strip()
            if not query:
                print("Search query cannot be empty.")
                continue
            results = search_shirts(shirts, query)
            if not results:
                print("No matching shirts found.")
            else:
                print(f"\nFound {len(results)} matching shirt(s):")
                for s in results:
                    img_indicator = " [📷]" if s.image_path else ""
                    print(f"  #{s.id}: {s.name} | {s.color} | {s.size} | {s.status}{img_indicator}")

        elif choice == "7":
            c = counts_by_status(shirts)
            total = len(shirts)
            print("\nShirt Counts:")
            for st in STATUSES:
                print(f"  {st}: {c.get(st, 0)}")
            print(f"  Total: {total}")

        elif choice == "8":
            stats = get_statistics(shirts)
            print("\n📊 INVENTORY STATISTICS")
            print("=" * 50)
            print(f"Total Shirts: {stats['total']}\n")
            
            print("By Status:")
            for status, count in stats['by_status'].items():
                print(f"  • {status}: {count}")
            
            print("\nBy Color:")
            for color, count in sorted(stats['by_color'].items()):
                print(f"  • {color}: {count}")
            
            print("\nBy Size:")
            for size, count in sorted(stats['by_size'].items()):
                print(f"  • {size}: {count}")
            
            print(f"\nShirts with Images: {stats['with_images']}")
            print(f"Shirts without Images: {stats['total'] - stats['with_images']}")

        elif choice == "0":
            save_shirts(shirts)
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please choose a number from the menu.")


def run_cli() -> None:
    # Alias for clearer import in main
    run()


