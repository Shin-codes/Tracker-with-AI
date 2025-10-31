from typing import List

from .models import Shirt, STATUSES
from .storage import load_shirts, save_shirts
from .inventory_manager import (
    add_shirt,
    update_status,
    delete_shirt,
    grouped_by_status,
    counts_by_status,
    find_by_id,
    view_grouped_inventory,
    count_by_status,
)


def _normalize_status(token: str) -> str:
    token = token.strip().lower()
    for st in STATUSES:
        if st.lower().startswith(token):
            return st
    return token.capitalize()


def show_help() -> None:
    print(
        """
Available commands:
  • add <color> <size> shirt to <status>
      Example: add red medium shirt to drawer
  • move <shirt name> to <status>
      Example: move red medium shirt to laundry
  • delete <shirt name>
      Example: delete red medium shirt
  • show inventory
      Displays all shirts grouped by status
  • count shirts
      Shows totals per status
  • help
      Displays this help message
  • exit / quit
      Exits chatbot mode
        """
    )


def process_message(message: str, shirts: List[Shirt]) -> None:
    msg = message.strip()
    low = msg.lower()

    if low in ("help", "?"):
        show_help()
        return

    if "add" in low and "shirt" in low:
        # Example: "add red medium shirt to drawer"
        try:
            words = low.split()
            # try to find pattern: add <color> <size> shirt to <status>
            add_idx = words.index("add")
            shirt_idx = words.index("shirt")
            color = words[add_idx + 1]
            size = words[add_idx + 2]
            status = STATUSES[0]
            if "to" in words:
                to_idx = words.index("to")
                status = _normalize_status(words[to_idx + 1])
            name = f"{color} {size}"
            s = add_shirt(shirts, name, color, size, status)
            save_shirts(shirts)
            print(f"Added a {color} {size} shirt to {status}. (#{s.id})")
        except Exception:
            print("Couldn't process that. Try: 'add red medium shirt to drawer'.")

    elif ("show" in low) or ("view" in low):
        groups = view_grouped_inventory(shirts)
        for status in STATUSES:
            items = groups.get(status, [])
            print(f"\n📦 {status} ({len(items)}):")
            if not items:
                print("  - None -")
            for s in items:
                print(f" - #{s['id']} {s['name']} ({s['color']}, {s['size']})")

    elif ("move" in low) or ("update" in low):
        # Example: "move red medium shirt to laundry"
        try:
            words = low.split()
            if "to" not in words:
                raise ValueError
            to_idx = words.index("to")
            new_status = _normalize_status(words[to_idx + 1])
            # name is everything between command and 'to'
            if words[0] in ("move", "update"):
                name_tokens = words[1:to_idx]
            else:
                name_tokens = words[:to_idx]
            name = " ".join([w for w in name_tokens if w not in ("shirt",)])
            # try to find by constructed name first, fallback by color+size heuristic
            target = None
            for s in shirts:
                if s.name.lower() == name.strip():
                    target = s
                    break
            if not target:
                # heuristic: name like "red medium"
                parts = name.split()
                if len(parts) >= 2:
                    color, size = parts[0], parts[1]
                    for s in shirts:
                        if s.color.lower() == color and s.size.lower() == size:
                            target = s
                            break
            if not target:
                print("Could not find that shirt.")
                return
            update_status(shirts, target.id, new_status)
            save_shirts(shirts)
            print(f"Moved {target.name} to {new_status}.")
        except Exception:
            print("Couldn't process. Try: 'move red medium shirt to laundry'.")

    elif ("delete" in low) or ("remove" in low):
        # Example: "delete red medium shirt"
        try:
            text = low.replace("delete", "").replace("remove", "").strip()
            text = text.replace("shirt", "").strip()
            # find by exact name or color+size
            target = None
            for s in shirts:
                if s.name.lower() == text:
                    target = s
                    break
            if not target:
                parts = text.split()
                if len(parts) >= 2:
                    color, size = parts[0], parts[1]
                    for s in shirts:
                        if s.color.lower() == color and s.size.lower() == size:
                            target = s
                            break
            if not target:
                print("Could not find that shirt.")
                return
            delete_shirt(shirts, target.id)
            save_shirts(shirts)
            print(f"🗑️ Deleted {target.name} from inventory.")
        except Exception:
            print("Couldn't process. Try: 'delete red medium shirt'.")

    elif ("count" in low) or ("how many" in low):
        counts = count_by_status(shirts)
        print("\n👕 Shirt Counts:")
        for status in STATUSES:
            print(f" - {status}: {counts.get(status, 0)}")
        print(f"Total: {len(shirts)}")

    else:
        print("Sorry, I didn't understand that command.")


def run_chatbot() -> None:
    shirts = load_shirts()
    print("\n🗣️ Shirt Inventory Chatbot Mode")
    print("Type 'help' to see commands. Type 'exit' to quit.\n")
    while True:
        msg = input("You: ")
        if msg.lower().strip() in ("exit", "quit"):
            print("Goodbye!")
            break
        process_message(msg, shirts)


