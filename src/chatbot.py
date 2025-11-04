"""
Enhanced Chatbot for Shirt Inventory Tracker.
Provides intent-based natural language processing with knowledge base support.
"""
import json
import os
from typing import List, Dict, Tuple, Optional
from difflib import SequenceMatcher

from .models import Shirt, STATUSES
from .storage import load_shirts, save_shirts
from .inventory_manager import (
    add_shirt,
    update_status,
    update_shirt,
    delete_shirt,
    grouped_by_status,
    counts_by_status,
    find_by_id,
    view_grouped_inventory,
    count_by_status,
    search_shirts,
    get_statistics,
)


# Intent definitions with keywords
INTENTS = {
    "add": ["add", "create", "new", "insert", "register"],
    "move": ["move", "update", "change", "transfer", "switch"],
    "search": ["find", "look", "search", "show me", "display", "list", "where"],
    "stats": ["count", "how many", "statistics", "stats", "analytics", "summary"],
    "delete": ["remove", "delete", "discard", "erase", "drop"],
    "view": ["show", "view", "display", "see", "list"],
    "help": ["help", "how", "guide", "explain", "tutorial", "what", "?"],
    "exit": ["exit", "quit", "bye", "goodbye", "close"],
}

# Load knowledge base
KNOWLEDGE_BASE: Dict[str, str] = {}


def _load_knowledge_base() -> Dict[str, str]:
    """Load knowledge base from JSON file."""
    global KNOWLEDGE_BASE
    if KNOWLEDGE_BASE:
        return KNOWLEDGE_BASE
    
    try:
        src_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(src_dir)
        kb_path = os.path.join(root_dir, "data", "knowledge_base.json")
        
        if os.path.exists(kb_path):
            with open(kb_path, "r", encoding="utf-8") as f:
                KNOWLEDGE_BASE = json.load(f)
        else:
            KNOWLEDGE_BASE = {}
    except Exception:
        KNOWLEDGE_BASE = {}
    
    return KNOWLEDGE_BASE


def _normalize_status(token: str) -> str:
    """Normalize status token to valid status."""
    token = token.strip().lower()
    for st in STATUSES:
        if st.lower().startswith(token):
            return st
    return token.capitalize()


def _detect_intent(message: str) -> Tuple[str, float]:
    """
    Detect user intent from message.
    Returns (intent_name, confidence_score)
    """
    msg_lower = message.lower().strip()
    
    # Direct keyword matching with confidence scoring
    best_intent = "unknown"
    best_score = 0.0
    
    for intent, keywords in INTENTS.items():
        for keyword in keywords:
            if keyword in msg_lower:
                # Calculate similarity score
                score = SequenceMatcher(None, keyword, msg_lower).ratio()
                if score > best_score:
                    best_score = score
                    best_intent = intent
                    break
    
    # Special cases for multi-word patterns
    if "how to" in msg_lower or "how do" in msg_lower:
        return ("help", 0.9)
    
    if ("show" in msg_lower or "view" in msg_lower) and "inventory" in msg_lower:
        return ("view", 0.95)
    
    if best_score < 0.3:
        return ("unknown", 0.0)
    
    return (best_intent, best_score)


def _lookup_knowledge_base(query: str) -> Optional[str]:
    """Look up information in knowledge base."""
    kb = _load_knowledge_base()
    query_lower = query.lower().strip()
    
    # Direct match
    if query_lower in kb:
        return kb[query_lower]
    
    # Fuzzy matching
    best_match = None
    best_score = 0.0
    
    for key, value in kb.items():
        score = SequenceMatcher(None, query_lower, key).ratio()
        if score > 0.6 and score > best_score:
            best_score = score
            best_match = value
    
    return best_match


def _format_help_message() -> str:
    """Format and return help message."""
    return """📋 Available Commands:

• Add a shirt: "add blue large shirt to drawer"
• Move shirt: "move blue shirt to laundry"
• Search: "search blue shirts" or "find red medium"
• View inventory: "show inventory" or "list all shirts"
• Count: "how many shirts" or "count shirts"
• Statistics: "statistics" or "show stats"
• Delete: "delete blue shirt"
• Help: "help" or ask "how to add shirt"

💡 You can ask questions like:
   - "how to upload image"
   - "how to edit shirt"
   - "what are statuses"
"""


def process_message(message: str, shirts: List[Shirt]) -> str:
    """
    Process user message and return response string.
    
    Args:
        message: User input message
        shirts: Current list of shirts
        
    Returns:
        Response string to display
    """
    if not message or not message.strip():
        return "Please enter a message. Type 'help' for available commands."
    
    msg = message.strip()
    low = msg.lower()
    
    # Detect intent
    intent, confidence = _detect_intent(msg)
    
    # Handle exit
    if intent == "exit" or low in ("exit", "quit", "bye"):
        return "👋 Goodbye! Thanks for using Shirt Inventory Tracker."
    
    # Handle help requests
    if intent == "help" or low in ("help", "?"):
        # Check if asking specific question
        if "how" in low or "what" in low:
            knowledge = _lookup_knowledge_base(msg)
            if knowledge:
                return f"💡 {knowledge}"
        return _format_help_message()
    
    # Handle add shirt
    if intent == "add" and "shirt" in low:
        try:
            words = low.split()
            if "add" not in words or "shirt" not in words:
                return "❌ Please specify: 'add [color] [size] shirt to [status]'\nExample: add red medium shirt to drawer"
            
            add_idx = words.index("add")
            shirt_idx = words.index("shirt")
            
            if shirt_idx <= add_idx + 1:
                return "❌ Please specify color and size. Example: add red medium shirt to drawer"
            
            color = words[add_idx + 1]
            size = words[add_idx + 2]
            status = STATUSES[0]  # Default
            
            if "to" in words:
                to_idx = words.index("to")
                if to_idx + 1 < len(words):
                    status = _normalize_status(words[to_idx + 1])
            
            name = f"{color} {size}"
            s = add_shirt(shirts, name, color, size, status)
            save_shirts(shirts)
            return f"✅ Added a {color} {size} shirt to {status}. (ID: #{s.id})"
        except (ValueError, IndexError) as e:
            return f"❌ Couldn't process that command. Try: 'add red medium shirt to drawer'"
        except Exception as e:
            return f"❌ Error adding shirt: {str(e)}"
    
    # Handle view/show inventory
    if intent == "view" or (("show" in low or "view" in low) and ("inventory" in low or "all" in low or "shirt" in low)):
        groups = view_grouped_inventory(shirts)
        
        if not shirts:
            return "📦 Your inventory is empty. Add some shirts to get started!"
        
        result = []
        for status in STATUSES:
            items = groups.get(status, [])
            result.append(f"\n📦 {status} ({len(items)}):")
            if not items:
                result.append("  - None -")
            else:
                for s in items:
                    img_indicator = " [📷]" if s.get('image_path') else ""
                    result.append(f"  • #{s['id']} {s['name']} ({s['color']}, {s['size']}){img_indicator}")
        
        return "\n".join(result)
    
    # Handle move/update status
    if intent == "move" and "to" in low:
        try:
            words = low.split()
            if "to" not in words:
                return "❌ Please specify destination status. Example: 'move blue shirt to laundry'"
            
            to_idx = words.index("to")
            if to_idx + 1 >= len(words):
                return "❌ Please specify a status. Valid statuses: In Drawer, Laundry, Worn"
            
            new_status = _normalize_status(words[to_idx + 1])
            if new_status not in STATUSES:
                return f"❌ Invalid status. Valid options: {', '.join(STATUSES)}"
            
            # Extract shirt name
            command_words = ["move", "update", "change", "transfer"]
            start_idx = 0
            for cmd in command_words:
                if cmd in words:
                    start_idx = words.index(cmd) + 1
                    break
            
            name_tokens = words[start_idx:to_idx]
            name = " ".join([w for w in name_tokens if w not in ("shirt", "the")]).strip()
            
            if not name:
                return "❌ Please specify which shirt to move. Example: 'move blue large shirt to laundry'"
            
            # Find shirt
            target = None
            for s in shirts:
                if s.name.lower() == name:
                    target = s
                    break
            
            if not target:
                # Try color+size matching
                parts = name.split()
                if len(parts) >= 2:
                    color, size = parts[0], parts[1]
                    for s in shirts:
                        if s.color.lower() == color and s.size.lower() == size:
                            target = s
                            break
            
            if not target:
                return f"❌ Could not find a shirt matching '{name}'. Use 'show inventory' to see all shirts."
            
            if target.status == new_status:
                return f"ℹ️ {target.name} is already in {new_status}."
            
            update_status(shirts, target.id, new_status)
            save_shirts(shirts)
            return f"✅ Moved {target.name} to {new_status}."
        except Exception as e:
            return f"❌ Couldn't process that. Try: 'move blue large shirt to laundry'"
    
    # Handle delete
    if intent == "delete" or intent == "remove":
        try:
            command_words = ["delete", "remove", "discard", "erase"]
            text = low
            for cmd in command_words:
                text = text.replace(cmd, "").strip()
            text = text.replace("shirt", "").replace("the", "").strip()
            
            if not text:
                return "❌ Please specify which shirt to delete. Example: 'delete blue large shirt'"
            
            # Find shirt
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
                return f"❌ Could not find a shirt matching '{text}'. Use 'show inventory' to see all shirts."
            
            delete_shirt(shirts, target.id)
            save_shirts(shirts)
            return f"🗑️ Deleted {target.name} from inventory."
        except Exception as e:
            return f"❌ Couldn't process that. Try: 'delete blue large shirt'"
    
    # Handle search
    if intent == "search" or ("search" in low and len(msg.split()) > 1):
        query = msg
        # Extract query after "search"
        if "search" in low:
            parts = low.split("search", 1)
            if len(parts) > 1:
                query = parts[1].strip()
        # Extract after other search keywords
        for keyword in ["find", "look for", "show me", "where is"]:
            if keyword in low:
                parts = low.split(keyword, 1)
                if len(parts) > 1:
                    query = parts[1].strip()
                    break
        
        if not query or not query.strip():
            return "❌ Please provide a search query. Example: 'search blue shirts' or 'find red medium'"
        
        results = search_shirts(shirts, query)
        if not results:
            return f"🔍 No shirts found matching '{query}'. Try different search terms or use 'show inventory' to see all shirts."
        
        response = [f"🔍 Found {len(results)} matching shirt(s):"]
        for s in results:
            img_indicator = " [📷]" if s.image_path else ""
            response.append(f"  • #{s.id} {s.name} ({s.color}, {s.size}) - {s.status}{img_indicator}")
        
        return "\n".join(response)
    
    # Handle count
    if intent == "stats" and ("count" in low or "how many" in low):
        counts = count_by_status(shirts)
        total = len(shirts)
        
        if total == 0:
            return "👕 You have no shirts in your inventory yet."
        
        response = ["👕 Shirt Counts:"]
        for status in STATUSES:
            count = counts.get(status, 0)
            response.append(f"  • {status}: {count}")
        response.append(f"\n📊 Total: {total}")
        
        return "\n".join(response)
    
    # Handle statistics
    if intent == "stats" and ("statistics" in low or "stats" in low or "analytics" in low):
        stats = get_statistics(shirts)
        
        if stats['total'] == 0:
            return "📊 Your inventory is empty. Add some shirts to see statistics!"
        
        response = [
            "📊 INVENTORY STATISTICS",
            "=" * 40,
            f"Total Shirts: {stats['total']}\n",
            "By Status:"
        ]
        
        for status, count in stats['by_status'].items():
            response.append(f"  • {status}: {count}")
        
        response.append("\nBy Color:")
        for color, count in sorted(stats['by_color'].items()):
            response.append(f"  • {color}: {count}")
        
        response.append("\nBy Size:")
        for size, count in sorted(stats['by_size'].items()):
            response.append(f"  • {size}: {count}")
        
        response.append(f"\n📷 Shirts with Images: {stats['with_images']}")
        response.append(f"📷 Shirts without Images: {stats['total'] - stats['with_images']}")
        
        return "\n".join(response)
    
    # Unknown command - try knowledge base
    knowledge = _lookup_knowledge_base(msg)
    if knowledge:
        return f"💡 {knowledge}"
    
    # Final fallback
    return f"❓ I'm not sure what you mean by '{msg}'. Type 'help' for available commands, or ask 'how to' questions about using the app."


def run_chatbot() -> None:
    """Run chatbot in CLI mode."""
    shirts = load_shirts()
    print("\n🗣️ Shirt Inventory Chatbot Mode")
    print("I'm your inventory assistant! Ask me about your shirts or type 'help' for commands.\n")
    
    while True:
        try:
            msg = input("You: ")
            if not msg.strip():
                continue
            
            if msg.lower().strip() in ("exit", "quit", "bye"):
                print("👋 Goodbye!")
                break
            
            response = process_message(msg, shirts)
            print(f"Bot: {response}\n")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}\n")
