from typing import List

from .models import Shirt, STATUSES
from .storage import load_shirts, save_shirts
from .inventory_manager import (
    add_shirt,
    grouped_by_status,
    update_status,
    delete_shirt,
    counts_by_status,
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
    print("4) Delete a shirt")
    print("5) Show counts")
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
                            print(
                                f"  #{s.id}: {s.name} | Color: {s.color} | Size: {s.size}"
                            )

        elif choice == "3":
            if not shirts:
                print("No shirts available.")
                continue
            for s in shirts:
                print(f"  #{s.id}: {s.name} | {s.color} | {s.size} | {s.status}")
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
                print(f"  #{s.id}: {s.name} | {s.color} | {s.size} | {s.status}")
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

        elif choice == "5":
            c = counts_by_status(shirts)
            total = len(shirts)
            print("\nShirt Counts:")
            for st in STATUSES:
                print(f"  {st}: {c.get(st, 0)}")
            print(f"  Total: {total}")

        elif choice == "0":
            save_shirts(shirts)
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please choose a number from the menu.")


